from jira.client import JIRA
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from .fields import Fields
from .projects import Projects
from .issues.types import IssueTypes
from .screens import Screens
from .workflows import Workflows
from .workflows.statuses import Statuses
from .groups import Groups

import os
import subprocess
import sys
import platform
import urllib.request
import logging
import shutil


def is_node_installed():
    """Check if Node.js is installed by running 'node -v'"""
    try:
        subprocess.run(["node", "-v"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def is_admin():
    """Check if the script is running with administrative privileges."""
    if platform.system() == "Windows":
        try:
            return subprocess.run(["net", "session"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).returncode == 0
        except subprocess.CalledProcessError:
            return False
    else:
        return os.geteuid() == 0  # Root user check for Linux/macOS


def get_npm_path():
    """Find the absolute path of npm"""
    if platform.system() == "Windows":
        os.environ["PATH"] += os.pathsep + f"{os.environ["ProgramFiles"]}\\nodejs"
        npm_path = shutil.which("npm.cmd")  # Windows uses npm.cmd
    else:
        npm_path = shutil.which("npm")  # Linux/macOS uses npm

    if npm_path:
        logging.info(f"Using npm from: {npm_path}")
        return npm_path
    else:
        logging.error("npm not found in PATH.")
        return None

def install_node_windows():
    """Download and install Node.js on Windows"""
    logging.info("Downloading Node.js installer for Windows...")
    node_installer_url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi"  # Update version as needed
    installer_path = os.path.join(os.environ["TEMP"], "nodejs_installer.msi")

    urllib.request.urlretrieve(node_installer_url, installer_path)
    logging.info(f"Installing Node.js from {installer_path}...")

    subprocess.run(["msiexec", "/i", installer_path, "/quiet", "/norestart"], check=True)
    os.remove(installer_path)
    logging.info("Node.js installed successfully. Please restart the shell if needed.")


def install_node_linux():
    """Install Node.js on Linux using package manager"""
    distro = platform.linux_distribution()[0].lower()

    logging.info("Installing Node.js on Linux...")
    if "ubuntu" in distro or "debian" in distro:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "nodejs", "npm"], check=True)
    elif "centos" in distro or "rhel" in distro or "fedora" in distro:
        subprocess.run(["sudo", "yum", "install", "-y", "nodejs", "npm"], check=True)
    else:
        logging.error("Unsupported Linux distribution. Please install Node.js manually.")
        raise Exception("Unsupported Linux distribution. Please install Node.js manually.")

    logging.info("Node.js installed successfully.")


def install_md_to_adf():
    """Install md-to-adf globally using npm"""
    npm_path = get_npm_path()
    if not npm_path:
        logging.error("npm is not installed or not in PATH. Please ensure Node.js is correctly installed.")
        raise Exception("npm is not installed or not in PATH. Please ensure Node.js is correctly installed.")
    try:
        logging.info("Installing md-to-adf...")
        subprocess.run([npm_path, "install", "-g", "md-to-adf"], check=True)
        logging.info("md-to-adf installed successfully.")
    except subprocess.CalledProcessError:
        logging.error("Failed to install md-to-adf.")
        raise Exception("Failed to install md-to-adf.")


if not is_node_installed():
    if not is_admin():
        logging.error("This script requires administrative privileges to install software.")
        logging.error("Please run as Administrator (Windows) or use 'sudo' (Linux).")
        raise Exception("Please run as Administrator (Windows) or use 'sudo' (Linux).")

    logging.info("Node.js is not installed.")
    if platform.system() == "Windows":
        install_node_windows()
    elif platform.system() == "Linux":
        install_node_linux()
    else:
        logging.error("Unsupported OS. Please install Node.js manually.")
        sys.exit(1)

logging.info("Node.js is installed.")
install_md_to_adf()

class JiraClient:
    """
    Represents a client for interacting with a Jira server.

    The `JiraClient` class enables interaction with a Jira server using its REST API.
    It allows users to perform operations like managing projects, issues, workflows,
    and retrieving user details. The class handles authentication and manages HTTP
    sessions to streamline communication with the Jira API.

    :ivar url: URL of the Jira server.
    :type url: str
    :ivar username: Username used for authentication with the Jira server.
    :type username: str
    :ivar password: Password used for authentication with the Jira server.
    :type password: str
    :ivar jira: Instance of a JIRA client for interacting with Jira server.
    :type jira: JIRA
    :ivar session: HTTP session for performing requests to the Jira server.
    :type session: requests.Session
    """
    def __init__(self, url, username, password):
        """
        Handles Jira connection and authentication.

        This class initializes a connection to a Jira server using both the `JIRA`
        library for direct interaction with Jira's functionalities and
        `requests` library for general API requests. It ensures the session is
        authenticated and prepared to interact with Jira's REST API. Authentication
        is performed using basic authentication.

        :param url: URL endpoint of the Jira server.
        :type url: str
        :param username: The username for Jira authentication.
        :type username: str
        :param password: The password associated with the username for Jira authentication.
        :type password: str
        """
        self.url = url
        self.username = username
        self.password = password
        self.jira = JIRA(server=self.url, basic_auth=(self.username, self.password))
        self.session = requests.Session()
        retries = Retry(
            total=5,  # Total number of retries
            backoff_factor=0.5,  # Backoff multiplier (e.g., 0.5, 1, 2, ...)
            status_forcelist=[500, 502, 503, 504],  # Retry on these HTTP status codes
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]  # Methods to retry
        )
        # Attach the retry logic to an HTTPAdapter
        adapter = HTTPAdapter(max_retries=retries)

        # Mount the adapter to the session
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.headers.update({"Content-Type": "application/json"})

    def close(self):
        """
        Closes the connections for JIRA and session objects.

        This method ensures that the resources utilized by the JIRA client and the
        session object are properly released and closed, avoiding potential
        resource leaks.

        :raises RuntimeError: Raised if an issue occurs during the connection close
          process.
        """
        self.jira.close()
        self.session.close()

    def fields(self) -> Fields:
        """
        Encapsulates the creation and retrieval process of a `Fields` instance and
        returns it. This method provides a seamless interface for handling
        field-related functionality.

        :return: An instance of the `Fields` class configured for the given context.
        :rtype: Fields
        """
        return Fields(self)

    def projects(self) -> Projects:
        """
        Provides access to the `Projects` instance associated with this object. This
        class method is responsible for returning an instance of the `Projects`
        class related to the current context. It facilitates interactions and
        operations that are defined under the `Projects` scope.

        :return: An instance of the `Projects` class associated with this object.
        :rtype: Projects
        """
        return Projects(self)

    def issue_types(self) -> IssueTypes:
        """
        Provides a method to retrieve supported issue types for the corresponding instance.
        This is a convenience method for returning IssueTypes associated with the instance.

        :return: An instance of the IssueTypes object, representing the available issue types
            for the instance.
        :rtype: IssueTypes
        """
        return IssueTypes(self)

    def screens(self) -> Screens:
        """
        Provides a method to instantiate and retrieve a `Screens` object
        that interacts with the parent context. This acts as a factory
        method returning the associated Screens instance for encapsulating
        functionality or data access related to screens.

        :return: A `Screens` object initialized with the current context.
        :rtype: Screens
        """
        return Screens(self)

    def statuses(self) -> Statuses:
        """
        Returns the Statuses object which encapsulates and provides access to
        available statuses within the calling context. This function operates
        as a constructor or a provider for the Statuses object.

        :return: An instance of the Statuses class providing access to and management
                 of statuses.
        :rtype: Statuses
        """
        return Statuses(self)

    def workflows(self) -> Workflows:
        """
        Returns an instance of the `Workflows` class to access its functionalities.

        The `workflows` method serves as a gateway to create and interact with an
        object of the `Workflows` class, providing its methods and properties.

        :rtype: Workflows
        :return: Instance of the `Workflows` class initialized with the current object.
        """
        return Workflows(self)

    def groups(self) -> Groups:
        """
        Provides functionality to retrieve the `Groups` object associated with the current
        context. This method returns an instance of the `Groups` class which encapsulates
        information or operations related to groups.

        :return: An instance of the `Groups` class.
        :rtype: Groups
        """
        return Groups(self)

    def get_me(self):
        """
        Fetches the details of the currently authenticated user. This method sends a GET request
        to the `/rest/api/3/myself` endpoint of the API to retrieve user-related data. If the
        request is successful, it processes and returns the JSON response. The response typically
        contains user information such as id, name, email, and other details.

        :param self: The instance of the class which contains the method and necessary attributes
                     or configurations for executing API requests.
        :return: The JSON response as a dictionary containing details of the authenticated user.
        :rtype: dict
        :raises HTTPError: If the HTTP request returns an unsuccessful status code.
        """
        resp = self.get("/rest/api/3/myself")
        resp.raise_for_status()
        return resp.json()

    def post(self, path, data):
        """
        Sends a POST request to the specified path with the given data.

        Constructs the full URL by appending the provided path to the base URL
        stored in `self.url`. The payload is serialized to JSON format before
        being sent.

        :param path: The path to append to the base URL for the POST request.
        :type path: str
        :param data: The data to send in the body of the POST request.
        :type data: dict
        :return: The response object resulting from the POST request.
        :rtype: requests.Response
        """
        url = f"{self.url.rstrip('/')}/{path.lstrip('/')}"
        return self.session.post(url, data=json.dumps(data))

    def delete(self, path):
        """
        Deletes a resource located at the specified path.

        This method sends a DELETE request to the provided path combined with
        the base URL defined in the `url` attribute of the instance.

        :param path: The specific endpoint path to append to the base URL for
                     sending the DELETE request.
        :type path: str

        :return: The response object resulting from the DELETE request.
        :rtype: requests.Response
        """
        url = f"{self.url.rstrip('/')}/{path.lstrip('/')}"
        return self.session.delete(url)

    def get(self, path):
        """
        Sends a GET request to the specified path appended to the configured base URL.

        This method constructs the full URL using the base URL instance variable and
        the specified path, then sends a GET request using the session object and
        returns the response.

        :param path: The endpoint or relative URL path to append to the base URL.
        :type path: str
        :return: The response object resulting from the GET request.
        :rtype: requests.Response
        """
        url = f"{self.url.rstrip('/')}/{path.lstrip('/')}"
        return self.session.get(url)

    def put(self, path, data):
        """
        Sends a PUT request to update a resource at the specified path with the given data.
        This method constructs a URL by appending the path to the base URL, then sends
        the request with the provided data as a JSON payload.

        :param path: The relative path of the resource to be updated.
        :type path: str
        :param data: The data to update the resource with, provided in dictionary format.
        :type data: dict
        :return: The server's response to the PUT request.
        :rtype: requests.Response
        """
        url = f"{self.url.rstrip('/')}/{path.lstrip('/')}"
        return self.session.put(url, data=json.dumps(data))