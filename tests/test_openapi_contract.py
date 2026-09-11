"""Structural conformance tests for the derived OpenAPI design projection."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import TypeGuard

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = REPOSITORY_ROOT / "openapi" / "openapi.json"
HTTP_METHODS = frozenset({"get", "head", "post", "put", "patch", "delete"})

HEALTH_OPERATIONS = frozenset(
    {
        ("/healthz/live", "get"),
        ("/healthz/live", "head"),
        ("/healthz/startup", "get"),
        ("/healthz/startup", "head"),
    }
)
PLUGIN_OPERATIONS = frozenset(
    {
        ("/api/v001/installations/current", "get"),
        ("/api/v001/groups", "get"),
        ("/api/v001/existing-public-photos", "get"),
        ("/api/v001/existing-public-photo-bindings", "post"),
        ("/api/v001/photo-bindings/{photoBindingId}/group-memberships", "get"),
        ("/api/v001/upload-authorizations", "post"),
        (
            "/api/v001/upload-authorizations/{uploadAuthorizationId}/photo-binding",
            "put",
        ),
        (
            "/api/v001/upload-authorizations/{uploadAuthorizationId}/ambiguity-candidates",
            "get",
        ),
        (
            "/api/v001/upload-authorizations/{uploadAuthorizationId}/ambiguity-resolution",
            "put",
        ),
        ("/api/v001/group-submission-batches", "post"),
        ("/api/v001/group-submission-intents", "get"),
        ("/api/v001/group-submission-intents/{submissionIntentId}", "get"),
    }
)
USER_OPERATIONS = frozenset(
    {
        ("/api/v001/plugin-codes", "get"),
        ("/api/v001/plugin-codes", "post"),
        ("/api/v001/plugin-codes/{pluginCodeId}", "patch"),
    }
)
ADMIN_OPERATIONS = frozenset(
    {
        ("/api/v001/admin/deployment", "get"),
        ("/api/v001/admin/session", "get"),
        ("/api/v001/admin/session/reauthentication", "post"),
        ("/api/v001/admin/session/logout", "post"),
        ("/api/v001/admin/sessions", "get"),
        ("/api/v001/admin/sessions/{sessionId}/revocation", "post"),
        ("/api/v001/admin/sessions/revoke-others", "post"),
        ("/api/v001/admin/flickr-connection", "get"),
        ("/api/v001/admin/flickr-connection/authorization", "post"),
        ("/api/v001/admin/flickr-connection/disconnection", "post"),
        ("/api/v001/admin/group-submission-intents", "get"),
        ("/api/v001/admin/group-submission-intents/{submissionIntentId}", "get"),
        ("/api/v001/admin/flickr-write-gates", "get"),
        ("/api/v001/admin/flickr-write-gates/{gateId}/resume", "post"),
        ("/api/v001/admin/audit-events", "get"),
    }
)


def load_openapi() -> dict[str, object]:
    """Load the checked-in JSON description."""
    return cast("dict[str, object]", json.loads(OPENAPI_PATH.read_text(encoding="utf-8")))


def iter_operations(
    document: dict[str, object],
) -> Iterator[tuple[str, str, dict[str, object]]]:
    """Yield every HTTP operation from the OpenAPI path map."""
    paths = cast("dict[str, object]", document["paths"])
    for path, raw_path_item in paths.items():
        path_item = cast("dict[str, object]", raw_path_item)
        for method, raw_operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            yield path, method, cast("dict[str, object]", raw_operation)


def iter_references(value: object) -> Iterator[str]:
    """Yield every JSON Reference in a parsed document."""
    if isinstance(value, dict):
        mapping = cast("dict[str, object]", value)
        reference = mapping.get("$ref")
        if isinstance(reference, str):
            yield reference
        for child in mapping.values():
            yield from iter_references(child)
    elif isinstance(value, list):
        for child in cast("list[object]", value):
            yield from iter_references(child)


def is_string_object_mapping(value: object) -> TypeGuard[dict[str, object]]:
    """Narrow a parsed JSON object to the mapping type used by these tests."""
    return isinstance(value, dict)


def heading_slugs(path: Path) -> set[str]:
    """Return the simple GitHub-style slugs used by referenced project headings."""
    slugs: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower()
        slug = re.sub(r"[^\w -]", "", heading).replace(" ", "-")
        slugs.add(slug)
    return slugs


class OpenApiContractTests(unittest.TestCase):
    def test_inventory_and_security_boundaries_are_exact(self) -> None:
        document = load_openapi()
        operations = {
            (path, method): operation for path, method, operation in iter_operations(document)
        }

        self.assertEqual(
            set(operations),
            set(HEALTH_OPERATIONS | PLUGIN_OPERATIONS | USER_OPERATIONS | ADMIN_OPERATIONS),
        )
        for key in HEALTH_OPERATIONS:
            self.assertEqual(operations[key]["security"], [], key)
        for key in PLUGIN_OPERATIONS:
            self.assertEqual(
                operations[key]["security"],
                [{"installationBearer": []}],
                key,
            )
        for key in USER_OPERATIONS:
            self.assertEqual(operations[key]["security"], [{"browserSessionCookie": []}], key)
        for key in ADMIN_OPERATIONS:
            if key == ("/api/v001/admin/session/logout", "post"):
                self.assertEqual(
                    operations[key]["security"],
                    [{}, {"browserSessionCookie": []}],
                    key,
                )
                continue
            self.assertEqual(operations[key]["security"], [{"browserSessionCookie": []}], key)

        components = cast("dict[str, object]", document["components"])
        security_schemes = cast("dict[str, object]", components["securitySchemes"])
        self.assertIn("browserSessionCookie", security_schemes)
        self.assertNotIn("adminCookie", security_schemes)

    def test_every_operation_is_sourced_unique_and_explicit_about_schema_status(
        self,
    ) -> None:
        document = load_openapi()
        operation_ids: set[str] = set()
        for path, method, operation in iter_operations(document):
            label = f"{method.upper()} {path}"
            operation_id = cast("str", operation["operationId"])
            self.assertNotIn(operation_id, operation_ids, label)
            operation_ids.add(operation_id)
            self.assertIn(operation["x-fga-schema-status"], {"closed", "not_closed"})
            self.assertIsInstance(operation.get("responses"), dict, label)

            sources = cast("list[str]", operation["x-fga-source"])
            self.assertTrue(sources, label)
            for source in sources:
                source_path, separator, anchor = source.partition("#")
                resolved_path = REPOSITORY_ROOT / source_path
                self.assertTrue(resolved_path.is_file(), source)
                if separator:
                    self.assertIn(anchor, heading_slugs(resolved_path), source)

    def test_every_internal_reference_resolves(self) -> None:
        document = load_openapi()
        for reference in iter_references(document):
            self.assertTrue(reference.startswith("#/"), reference)
            current: object = document
            for raw_segment in reference.removeprefix("#/").split("/"):
                segment = raw_segment.replace("~1", "/").replace("~0", "~")
                if not is_string_object_mapping(current):
                    self.fail(reference)
                current = current[segment]

    def test_browser_mutations_require_csrf_and_no_bypass_routes_exist(
        self,
    ) -> None:
        document = load_openapi()
        operations = {
            (path, method): operation for path, method, operation in iter_operations(document)
        }
        csrf_reference = {"$ref": "#/components/parameters/BrowserSessionCsrf"}
        for path, method in ADMIN_OPERATIONS | USER_OPERATIONS:
            if method == "get":
                continue
            operation = operations[(path, method)]
            self.assertTrue(operation["x-fga-csrf-required"] is True, path)
            parameters = cast("list[object]", operation.get("parameters", []))
            self.assertIn(csrf_reference, parameters, path)

        paths = "\n".join(cast("dict[str, object]", document["paths"]))
        for forbidden in (
            "flickr-api-proxy",
            "groups.pools.remove",
            "clear-block",
            "force-resubmit",
            "retry-now",
            "/reopen",
        ):
            self.assertNotIn(forbidden, paths)

        non_openapi = set(cast("list[str]", document["x-fga-non-openapi-routes"]))
        self.assertEqual(
            non_openapi,
            {
                "/admin/",
                "/admin/flickr-oauth/callback",
                "/admin/google-login",
                "/admin/login",
            },
        )
        self.assertEqual(document["x-fga-unresolved-route-roles"], [])

    def test_browser_session_lifecycle_shapes_are_closed(self) -> None:
        document = load_openapi()
        paths = cast("dict[str, object]", document["paths"])
        components = cast("dict[str, object]", document["components"])
        schemas = cast("dict[str, object]", components["schemas"])

        current_path = cast("dict[str, object]", paths["/api/v001/admin/session"])
        current = cast("dict[str, object]", current_path["get"])
        self.assertEqual(current["x-fga-schema-status"], "closed")

        reauth_path = cast(
            "dict[str, object]",
            paths["/api/v001/admin/session/reauthentication"],
        )
        reauth = cast("dict[str, object]", reauth_path["post"])
        self.assertEqual(reauth["x-fga-schema-status"], "closed")
        self.assertTrue(reauth["x-fga-exact-origin-required"] is True)
        self.assertNotIn("x-fga-recent-auth-required", reauth)

        logout_path = cast(
            "dict[str, object]",
            paths["/api/v001/admin/session/logout"],
        )
        logout = cast("dict[str, object]", logout_path["post"])
        self.assertTrue(logout["x-fga-exact-origin-required"] is True)

        for path in (
            "/api/v001/admin/sessions/{sessionId}/revocation",
            "/api/v001/admin/sessions/revoke-others",
        ):
            path_item = cast("dict[str, object]", paths[path])
            operation = cast("dict[str, object]", path_item["post"])
            self.assertEqual(operation["x-fga-schema-status"], "closed")
            self.assertTrue(operation["x-fga-recent-auth-required"] is True)
            self.assertEqual(
                set(cast("dict[str, object]", operation["responses"])),
                {"204", "401", "403", "409", "default"},
            )

        token = cast("dict[str, object]", schemas["Random256Base64Url"])
        self.assertEqual(token["pattern"], "^[A-Za-z0-9_-]{43}$")
        page = cast("dict[str, object]", schemas["AdministrativeSessionPage"])
        page_properties = cast("dict[str, object]", page["properties"])
        sessions = cast("dict[str, object]", page_properties["sessions"])
        self.assertEqual(sessions["maxItems"], 50)

    def test_plugin_code_collection_and_member_contract_is_explicit(self) -> None:
        document = load_openapi()
        tag_names = {
            cast("str", cast("dict[str, object]", tag)["name"])
            for tag in cast("list[object]", document["tags"])
        }
        self.assertIn("Plugin Codes", tag_names)
        self.assertNotIn("Administrative installations", tag_names)
        paths = cast("dict[str, object]", document["paths"])
        self.assertIn("/api/v001/plugin-codes", paths)
        self.assertIn("/api/v001/plugin-codes/{pluginCodeId}", paths)

        self.assertNotIn("/api/v001/plugin-code", paths)
        self.assertNotIn("/api/v001/plugin-codes/", paths)
        self.assertFalse(any(path.startswith("/api/v001/admin/installations") for path in paths))

        collection = cast("dict[str, object]", paths["/api/v001/plugin-codes"])
        self.assertEqual(set(collection), {"get", "post"})
        get = cast("dict[str, object]", collection["get"])
        self.assertIn("fgaUserId", cast("str", get["description"]))
        self.assertIn("email is never", cast("str", get["description"]))
        self.assertEqual(get["x-fga-audit"], "durable_before_success_response")
        self.assertEqual(
            get["parameters"],
            [
                {"$ref": "#/components/parameters/OptionalPageSize"},
                {"$ref": "#/components/parameters/PluginCodePageToken"},
            ],
        )
        post = cast("dict[str, object]", collection["post"])
        self.assertEqual(
            set(cast("dict[str, object]", post["responses"])),
            {"201", "401", "default"},
        )
        self.assertTrue(post["x-fga-recent-auth-required"] is True)
        self.assertTrue(post["x-fga-exact-origin-required"] is True)
        self.assertEqual(post["x-fga-audit"], "same_database_transaction")

        member = cast(
            "dict[str, object]",
            paths["/api/v001/plugin-codes/{pluginCodeId}"],
        )
        self.assertEqual(set(member), {"parameters", "patch"})
        patch = cast("dict[str, object]", member["patch"])
        self.assertEqual(patch["x-fga-audit"], "same_database_transaction")
        self.assertIn(
            {"$ref": "#/components/parameters/PluginCodeIfMatch"},
            cast("list[object]", patch["parameters"]),
        )
        request_body = cast("dict[str, object]", patch["requestBody"])
        content = cast("dict[str, object]", request_body["content"])
        self.assertEqual(set(content), {"application/merge-patch+json"})

        components = cast("dict[str, object]", document["components"])
        schemas = cast("dict[str, object]", components["schemas"])
        state_patch = cast("dict[str, object]", schemas["PluginCodeStatePatch"])
        self.assertTrue(state_patch["additionalProperties"] is False)
        self.assertEqual(state_patch["required"], ["state"])
        properties = cast("dict[str, object]", state_patch["properties"])
        self.assertEqual(properties["state"], {"type": "string", "const": "revoked"})

    def test_plugin_code_creation_response_uses_exact_canonical_spelling(self) -> None:
        document = load_openapi()
        paths = cast("dict[str, object]", document["paths"])
        collection = cast("dict[str, object]", paths["/api/v001/plugin-codes"])
        post = cast("dict[str, object]", collection["post"])
        post_responses = cast("dict[str, object]", post["responses"])
        self.assertEqual(
            post_responses["201"],
            {"$ref": "#/components/responses/PluginCodeCreated"},
        )

        components = cast("dict[str, object]", document["components"])
        schemas = cast("dict[str, object]", components["schemas"])
        plugin_code = cast("dict[str, object]", schemas["PluginCodeCredential"])
        self.assertEqual(plugin_code["minLength"], 64)
        self.assertEqual(plugin_code["maxLength"], 64)
        self.assertEqual(
            plugin_code["pattern"],
            "^[0-9A-HJKMNP-TV-Z]{4}(?:-[0-9A-HJKMNP-TV-Z]{4}){11}-[0-9A-HJKMNP-TV-Z]{3}[0G]$",
        )
        plugin_code_pattern = re.compile(cast("str", plugin_code["pattern"]))
        canonical_example = "2345-6789-ABCD-EFGH-JKMN-PQRS-TVWX-YZ23-4567-89AB-CDEF-GHJK-MNP0"
        self.assertIsNotNone(plugin_code_pattern.fullmatch(canonical_example))
        for noncanonical in (
            canonical_example.lower(),
            canonical_example.replace("-", "", 1),
            f" {canonical_example}",
            canonical_example[:-1] + "1",
            canonical_example.replace("0", "O"),
        ):
            self.assertIsNone(plugin_code_pattern.fullmatch(noncanonical), noncanonical)

        creation = cast("dict[str, object]", schemas["PluginCodeCreation"])
        self.assertTrue(creation["additionalProperties"] is False)
        self.assertEqual(
            creation["required"],
            ["schemaVersion", "pluginCodeId", "pluginCode"],
        )
        creation_properties = cast("dict[str, object]", creation["properties"])
        self.assertEqual(
            creation_properties["pluginCode"],
            {"$ref": "#/components/schemas/PluginCodeCredential"},
        )

    def test_courtesy_and_permanent_protection_shapes_are_fixed(self) -> None:
        document = load_openapi()
        components = cast("dict[str, object]", document["components"])
        schemas = cast("dict[str, object]", components["schemas"])
        batch_request = cast("dict[str, object]", schemas["GroupSubmissionBatchRequest"])
        properties = cast("dict[str, object]", batch_request["properties"])
        group_ids = cast("dict[str, object]", properties["flickrGroupIds"])
        self.assertEqual(group_ids["minItems"], 1)
        self.assertEqual(group_ids["maxItems"], 60)
        self.assertTrue(group_ids["uniqueItems"] is True)

        attention = cast("dict[str, object]", schemas["Attention"])
        attention_properties = cast("dict[str, object]", attention["properties"])
        resubmission = cast("dict[str, object]", attention_properties["fgaResubmissionAllowed"])
        self.assertTrue(resubmission["const"] is False)


if __name__ == "__main__":
    unittest.main()
