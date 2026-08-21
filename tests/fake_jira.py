"""
A stateful in-memory stand-in for the Jira Cloud endpoints jirakit deploys to.

The unit tests elsewhere assert which requests were issued. Reconciliation
cannot be tested that way: whether applying a template twice is safe depends on
what the site holds after the first run, so the second run has to be answered
from real state. This fake holds that state and records every request, so a test
can assert both the resulting configuration and that nothing was written.
"""

import json

import requests


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)


def paginated(values):
    return {"isLast": True, "startAt": 0, "maxResults": 50, "total": len(values), "values": values}


class FakeJira:
    """Holds site state and answers the endpoints a template deployment uses."""

    def __init__(self):
        self.all_fields = {}
        self.all_issue_types = {}
        self.issue_type_schemes = {}
        self.all_screens = {}
        self.tabs = {}  # screen_id -> {tab_id: {"name": str, "fields": [id]}}
        self.screen_schemes = {}
        self.issue_type_screen_schemes = {}
        self.all_workflows = {}
        self.workflow_schemes = {}
        self.all_groups = {}
        self.all_statuses = {}
        self.workflow_versions = {}
        self.project = None
        self.project_issue_type_scheme = None
        self.project_issue_type_screen_scheme = None
        self.project_workflow_scheme = None
        self.calls = []
        self.payloads = []
        # Both create metadata endpoints page, and default to 50. Modelling
        # that is what lets a test see a truncated read; returning everything
        # in one page would make the fake structurally unable to express it.
        self.createmeta_page_size = 50
        self._seq = 10000

    # -- helpers ------------------------------------------------------------

    def _id(self):
        self._seq += 1
        return str(self._seq)

    def payload(self, path):
        """The body of the last POST to a path, for asserting what was sent."""
        for sent_path, data in reversed(self.payloads):
            if sent_path == path:
                return data
        raise AssertionError(f"nothing was posted to {path}")

    def writes(self):
        return [c for c in self.calls if not c.startswith("GET ")]

    def creations(self):
        return [c for c in self.calls if c.startswith("POST ")]

    def tab_named(self, screen_name, tab_name):
        screen_id = next(
            sid for sid, s in self.all_screens.items() if s["name"] == screen_name
        )
        for tab in self.tabs.get(screen_id, {}).values():
            if tab["name"] == tab_name:
                return tab
        raise AssertionError(
            f"no tab {tab_name!r} on {screen_name!r}; have {self.tabs.get(screen_id)}"
        )

    def named(self, collection, name):
        return [v for v in collection.values() if v.get("name") == name]


    def createmeta_fields(self, issue_type_id):
        """
        The fields an issue type's create metadata exposes.

        Derived from screen tab membership rather than stored separately,
        because that is what determines it on a real site: Jira registers a
        field with createmeta when the field is added to a tab of a screen wired
        to the project. Modelling it any other way would let a test pass while
        the behaviour it exists to check was broken.
        """
        itss = self.issue_type_screen_schemes.get(
            self.project_issue_type_screen_scheme
        )
        if not itss:
            return []

        screen_scheme_id = None
        for mapping in itss["mappings"]:
            if mapping["issueTypeId"] == issue_type_id:
                screen_scheme_id = mapping["screenSchemeId"]
                break
        else:
            for mapping in itss["mappings"]:
                if mapping["issueTypeId"] == "default":
                    screen_scheme_id = mapping["screenSchemeId"]
                    break

        screen_scheme = self.screen_schemes.get(screen_scheme_id)
        if not screen_scheme:
            return []

        screen_id = screen_scheme.get("screens", {}).get("default")
        field_ids = []
        for tab in self.tabs.get(screen_id, {}).values():
            field_ids.extend(tab["fields"])
        return field_ids


    def createmeta_page(self, path, items, key):
        """Serve one page of a create metadata endpoint, honouring startAt."""
        start_at = 0
        max_results = self.createmeta_page_size
        if "startAt=" in path:
            start_at = int(path.split("startAt=")[1].split("&")[0])
        if "maxResults=" in path:
            max_results = min(
                int(path.split("maxResults=")[1].split("&")[0]),
                self.createmeta_page_size,
            )
        window = items[start_at : start_at + max_results]
        return FakeResponse(
            {
                "startAt": start_at,
                "maxResults": max_results,
                "total": len(items),
                key: window,
            }
        )

    # -- verbs --------------------------------------------------------------

    def get(self, path=None, **kwargs):
        self.calls.append(f"GET {path}")
        base = path.split("?")[0]

        if base == "/rest/api/3/field/search":
            return FakeResponse(paginated(list(self.all_fields.values())))
        if base.startswith("/rest/api/3/field/") and base.endswith("/context"):
            return FakeResponse(paginated([{"id": "ctx-1", "name": "Default"}]))
        if base == "/rest/api/3/issuetype":
            return FakeResponse(list(self.all_issue_types.values()))
        if base == "/rest/api/3/issuetype/project":
            return FakeResponse(list(self.all_issue_types.values()))
        if base == "/rest/api/3/issuetypescreenscheme/project":
            assigned = self.issue_type_screen_schemes.get(
                self.project_issue_type_screen_scheme
            )
            return FakeResponse(paginated([assigned] if assigned else []))
        if base == "/rest/api/3/issuetypescheme/project":
            assigned = self.issue_type_schemes.get(self.project_issue_type_scheme)
            return FakeResponse(
                paginated(
                    [{"issueTypeScheme": assigned, "projectIds": [self.project["id"]]}]
                    if assigned
                    else []
                )
            )
        if base == "/rest/api/3/issuetypescreenscheme":
            return FakeResponse(paginated(list(self.issue_type_screen_schemes.values())))
        if base == "/rest/api/3/issuetypescheme":
            return FakeResponse(paginated(list(self.issue_type_schemes.values())))
        if base == "/rest/api/3/screenscheme":
            if "id=" in path:
                wanted = path.split("id=")[1].split("&")[0]
                return FakeResponse(
                    paginated(
                        [s for s in self.screen_schemes.values() if s["id"] == wanted]
                    )
                )
            return FakeResponse(paginated(list(self.screen_schemes.values())))
        if base == "/rest/api/3/screens":
            if "id=" in path:
                wanted = path.split("id=")[1].split("&")[0]
                return FakeResponse(
                    paginated([s for s in self.all_screens.values() if s["id"] == wanted])
                )
            return FakeResponse(paginated(list(self.all_screens.values())))
        if base.endswith("/fields") and "/tabs/" in base:
            screen_id = base.split("/screens/")[1].split("/tabs/")[0]
            tab_id = base.split("/tabs/")[1].split("/fields")[0]
            tab = self.tabs.get(screen_id, {}).get(tab_id, {"fields": []})
            return FakeResponse(
                [{"id": f, "name": self.all_fields.get(f, {}).get("name", f)} for f in tab["fields"]]
            )
        if base.endswith("/tabs"):
            screen_id = base.split("/screens/")[1].split("/tabs")[0]
            return FakeResponse(
                [
                    {"id": tid, "name": t["name"]}
                    for tid, t in self.tabs.get(screen_id, {}).items()
                ]
            )
        if base == "/rest/api/3/statuses/search":
            return FakeResponse(paginated(list(self.all_statuses.values())))
        if base == "/rest/api/3/workflow/search":
            return FakeResponse(paginated(list(self.all_workflows.values())))
        if base == "/rest/api/3/workflowscheme":
            return FakeResponse(paginated(list(self.workflow_schemes.values())))
        if base.startswith("/rest/api/3/workflowscheme/project"):
            scheme = self.workflow_schemes.get(self.project_workflow_scheme)
            return FakeResponse(
                {"values": [{"workflowScheme": scheme}] if scheme else []}
            )
        if "/rest/api/3/issue/createmeta/" in base and "/issuetypes" in base:
            after = base.split("/issuetypes")[1].strip("/")
            if after:
                return self.createmeta_page(
                    path,
                    [
                        {
                            "fieldId": f,
                            "name": self.all_fields.get(f, {}).get("name", f),
                        }
                        for f in self.createmeta_fields(after)
                    ],
                    "fields",
                )
            return self.createmeta_page(
                path,
                [
                    {"id": i["id"], "name": i["name"]}
                    for i in self.all_issue_types.values()
                ],
                "issueTypes",
            )
        if base == "/rest/api/3/group/bulk":
            return FakeResponse(paginated(list(self.all_groups.values())))
        if base.startswith("/rest/api/3/project/"):
            return FakeResponse(self.project or {})

        raise AssertionError(f"unexpected GET {path}")

    def post(self, path=None, data=None, **kwargs):
        self.calls.append(f"POST {path}")
        self.payloads.append((path, data))
        data = data or {}

        if path == "/rest/api/3/project":
            self.project = {"id": self._id(), "key": data["key"], "name": data["name"]}
            return FakeResponse(self.project, 201)

        if path == "/rest/api/3/group":
            self.all_groups[data["name"]] = {"name": data["name"], "groupId": self._id()}
            return FakeResponse(self.all_groups[data["name"]], 201)

        if path == "/rest/api/3/field":
            field_id = f"customfield_{self._id()}"
            self.all_fields[field_id] = {
                "id": field_id,
                "name": data["name"],
                "description": data.get("description", ""),
                "custom": True,
                "schema": {"custom": data.get("type", "")},
            }
            return FakeResponse(self.all_fields[field_id], 201)

        if path == "/rest/api/3/issuetype":
            new_id = self._id()
            self.all_issue_types[new_id] = {
                "id": new_id,
                "name": data["name"],
                "description": data.get("description", ""),
                "hierarchyLevel": data.get("hierarchyLevel", 0),
            }
            return FakeResponse(self.all_issue_types[new_id], 201)

        if path == "/rest/api/3/issuetypescheme":
            new_id = self._id()
            self.issue_type_schemes[new_id] = {
                "id": new_id,
                "name": data["name"],
                "isDefault": False,
                "issueTypeIds": list(data.get("issueTypeIds", [])),
            }
            return FakeResponse({"issueTypeSchemeId": new_id}, 201)

        if path == "/rest/api/3/screens":
            new_id = self._id()
            self.all_screens[new_id] = {
                "id": new_id,
                "name": data["name"],
                "description": data.get("description", ""),
            }
            self.tabs.setdefault(new_id, {})
            return FakeResponse(self.all_screens[new_id], 201)

        if path == "/rest/api/3/screenscheme":
            new_id = self._id()
            self.screen_schemes[new_id] = {
                "id": new_id,
                "name": data["name"],
                "description": data.get("description", ""),
                "screens": data.get("screens", {}),
            }
            return FakeResponse(self.screen_schemes[new_id], 201)

        if path == "/rest/api/3/issuetypescreenscheme":
            new_id = self._id()
            self.issue_type_screen_schemes[new_id] = {
                "id": new_id,
                "name": data["name"],
                "mappings": list(data.get("issueTypeMappings", [])),
            }
            return FakeResponse(self.issue_type_screen_schemes[new_id], 201)

        if path == "/rest/api/3/workflowscheme":
            new_id = self._id()
            self.workflow_schemes[new_id] = {
                "id": new_id,
                "name": data["name"],
                "issueTypeMappings": dict(data.get("issueTypeMappings", {})),
            }
            return FakeResponse(self.workflow_schemes[new_id], 201)

        if path == "/rest/api/3/statuses":
            new_id = self._id()
            record = {
                "id": new_id,
                "name": data["statuses"][0]["name"]
                if "statuses" in data
                else data.get("name"),
                "statusCategory": data["statuses"][0]["statusCategory"]
                if "statuses" in data
                else data.get("statusCategory"),
            }
            self.all_statuses[new_id] = record
            return FakeResponse([record], 201)

        if path == "/rest/api/3/workflows":
            wanted = data.get("workflowIds", [])
            return FakeResponse(
                {
                    "workflows": [
                        {
                            "id": wid,
                            "name": self.all_workflows[wid]["name"],
                            "version": self.workflow_versions[wid],
                        }
                        for wid in wanted
                        if wid in self.all_workflows
                    ]
                }
            )

        if path == "/rest/api/3/workflows/update/validation":
            return FakeResponse({"errors": []})

        if path == "/rest/api/3/workflows/update":
            updated = []
            for workflow in data.get("workflows", []):
                wid = workflow["id"]
                # The real endpoint uses the version for optimistic locking and
                # rejects an update that omits it or carries a stale one.
                version = workflow.get("version")
                if not version:
                    return FakeResponse(
                        {"errorMessages": ["version is required"]}, 400
                    )
                if version.get("versionNumber") != self.workflow_versions[wid][
                    "versionNumber"
                ]:
                    return FakeResponse(
                        {"errorMessages": ["version mismatch"]}, 409
                    )
                self.all_workflows[wid]["description"] = workflow.get("description", "")
                self.all_workflows[wid]["transitions"] = workflow.get("transitions", [])
                version = self.workflow_versions[wid]
                version["versionNumber"] += 1
                updated.append({"id": wid, "name": self.all_workflows[wid]["name"]})
            return FakeResponse({"workflows": updated})

        if path == "/rest/api/3/workflows/create/validation":
            return FakeResponse({"errors": []})

        if path == "/rest/api/3/workflows/create":
            created = []
            for workflow in data.get("workflows", []):
                new_id = self._id()
                self.all_workflows[new_id] = {
                    "id": {"entityId": new_id, "name": workflow["name"]},
                    "name": workflow["name"],
                    "description": workflow.get("description", ""),
                    "transitions": workflow.get("transitions", []),
                }
                self.workflow_versions[new_id] = {
                    "id": f"v-{new_id}",
                    "versionNumber": 1,
                }
                created.append({"id": new_id, "name": workflow["name"]})
            return FakeResponse({"workflows": created}, 201)

        if "/tabs/" in path and path.endswith("/fields"):
            screen_id = path.split("/screens/")[1].split("/tabs/")[0]
            tab_id = path.split("/tabs/")[1].split("/fields")[0]
            self.tabs[screen_id][tab_id]["fields"].append(data["fieldId"])
            return FakeResponse({}, 201)

        if path.endswith("/tabs"):
            screen_id = path.split("/screens/")[1].split("/tabs")[0]
            tab_id = self._id()
            self.tabs.setdefault(screen_id, {})[tab_id] = {
                "name": data["name"],
                "fields": [],
            }
            return FakeResponse({"id": tab_id, "name": data["name"]}, 201)

        if "/context/" in path and path.endswith("/option"):
            return FakeResponse({}, 201)

        raise AssertionError(f"unexpected POST {path}")

    def put(self, path=None, data=None, **kwargs):
        self.calls.append(f"PUT {path}")
        data = data or {}

        if path == "/rest/api/3/issuetypescheme/project":
            self.project_issue_type_scheme = data.get("issueTypeSchemeId")
            return FakeResponse({})
        if path == "/rest/api/3/issuetypescreenscheme/project":
            self.project_issue_type_screen_scheme = data.get("issueTypeScreenSchemeId")
            return FakeResponse({})
        if path == "/rest/api/3/workflowscheme/project":
            self.project_workflow_scheme = data.get("workflowSchemeId")
            return FakeResponse({})
        if path.startswith("/rest/api/3/issuetypescheme/") and path.endswith(
            "/issuetype"
        ):
            scheme_id = path.split("/issuetypescheme/")[1].split("/issuetype")[0]
            self.issue_type_schemes[scheme_id]["issueTypeIds"].extend(
                data.get("issueTypeIds", [])
            )
            return FakeResponse({})
        if path.startswith("/rest/api/3/issuetypescreenscheme/") and path.endswith(
            "/mapping"
        ):
            scheme_id = path.split("/issuetypescreenscheme/")[1].split("/mapping")[0]
            self.issue_type_screen_schemes[scheme_id]["mappings"].extend(
                data.get("issueTypeMappings", [])
            )
            return FakeResponse({})
        if "/workflowscheme/" in path and "/issuetype/" in path:
            scheme_id = path.split("/workflowscheme/")[1].split("/issuetype/")[0]
            issue_type_id = path.split("/issuetype/")[1]
            self.workflow_schemes[scheme_id]["issueTypeMappings"][issue_type_id] = data[
                "workflow"
            ]
            return FakeResponse({})

        raise AssertionError(f"unexpected PUT {path}")

    def delete(self, path=None, **kwargs):
        self.calls.append(f"DELETE {path}")
        return FakeResponse({})

    # -- client surface -----------------------------------------------------

    def get_me(self):
        return {"accountId": "account-1", "emailAddress": "test@example.com"}


class FakeClient(FakeJira):
    """
    FakeJira with the manager accessors JiraClient exposes.

    The managers are the real ones, so a test exercising this runs the actual
    reconciliation logic against in-memory state rather than against assertions
    about which requests were made.
    """

    def fields(self):
        from jirakit.fields import Fields

        return Fields(self)

    def screens(self):
        from jirakit.screens import Screens

        return Screens(self)

    def issue_types(self):
        from jirakit.issues.types import IssueTypes

        return IssueTypes(self)

    def workflows(self):
        from jirakit.workflows import Workflows

        return Workflows(self)

    def groups(self):
        from jirakit.groups import Groups

        return Groups(self)

    def statuses(self):
        from jirakit.workflows.statuses import Statuses

        return Statuses(self)
