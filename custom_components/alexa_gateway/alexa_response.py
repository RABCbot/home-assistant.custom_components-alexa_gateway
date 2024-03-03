# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import random
import uuid

from .utils import get_utc_timestamp


class AlexaResponse:

    def __init__(self, **kwargs):

        self.context_properties = []
        self.payload_endpoints = []
        self.payload_properties = []
        self.payload_timestamp = None

        # Set up the response structure
        self.context = {}
        self.event = {
            "header": {
                "namespace": kwargs.get("namespace", "Alexa"),
                "name": kwargs.get("name", "Response"),
                "messageId": str(uuid.uuid4()),
                "payloadVersion": kwargs.get("payload_version", "3")
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": kwargs.get("scope_token", "INVALID")
                },
                "endpointId": kwargs.get("endpoint_id", "INVALID")
            },
            "payload": kwargs.get("payload", {})
        }

        if "correlation_token" in kwargs:
            self.event["header"]["correlationToken"] = kwargs.get("correlation_token", "INVALID")

        if "cookie" in kwargs:
            self.event["endpoint"]["cookie"] = kwargs.get("cookie", "{}")

        # No endpoint in an AcceptGrant or Discover request
        if self.event["header"]["name"] == "AcceptGrant.Response" or self.event["header"]["name"] == "Discover.Response":
            self.event.pop("endpoint")

    def add_context_property(self, **kwargs):
        self.context_properties.append(self.create_property(**kwargs))

    def add_payload_property(self, **kwargs):
        self.payload_properties.append(self.create_property(**kwargs))

    def add_cookie(self, key, value):

        if "cookies" in self is None:
            self.cookies = {}

        self.cookies[key] = value

    def add_payload_endpoint(self, **kwargs):
        self.payload_endpoints.append(self.create_payload_endpoint(**kwargs))

    def add_payload_timestamp(self):
        self.payload_timestamp = get_utc_timestamp()

    def create_property(self, **kwargs):
        prop = {
            "namespace": kwargs.get("namespace", "Alexa.EndpointHealth"),
            "name": kwargs.get("name", "connectivity"),
            "value": kwargs.get("value", {"value": "OK"}),
            "timeOfSample": get_utc_timestamp(),
            "uncertaintyInMilliseconds": kwargs.get("uncertainty_in_milliseconds", 0)
        }
        instance = kwargs.get("instance", None)
        if instance:
            prop["instance"] = instance

        return prop

    def create_payload_endpoint(self, **kwargs):
        # Return the proper structure expected for the endpoint
        endpoint = {
            "capabilities": kwargs.get("capabilities", []),
            "description": kwargs.get("description", "Sample Endpoint Description"),
            "displayCategories": kwargs.get("display_categories", ["OTHER"]),
            "endpointId": kwargs.get("endpoint_id", "endpoint_" + "%0.6d" % random.randint(0, 999999)),
            "friendlyName": kwargs.get("friendly_name", "Sample Endpoint"),
            "manufacturerName": kwargs.get("manufacturer_name", "Sample Manufacturer")
        }

        if "cookie" in kwargs:
            endpoint["cookie"] = kwargs.get("cookie", {})

        return endpoint

    def create_payload_endpoint_capability(self, **kwargs):
        capability = {
            "type": kwargs.get("type", "AlexaInterface"),
            "interface": kwargs.get("interface", "Alexa"),
            "version": kwargs.get("version", "3")
        }

        instance = kwargs.get("instance", None)
        if instance:
            capability["instance"] = instance

        supportsDeactivation = kwargs.get("supports_deactivation", None)
        if supportsDeactivation:
            capability["supportsDeactivation"] = supportsDeactivation

        proactively_reported = kwargs.get("proactively_reported", None)
        supported = kwargs.get("supported", None)
        if proactively_reported and not supported:
            capability["proactivelyReported"] = proactively_reported
        if supported:
            capability["properties"] = {}
            capability["properties"]["supported"] = supported
            capability["properties"]["proactivelyReported"] = kwargs.get("proactively_reported", False)
            capability["properties"]["retrievable"] = kwargs.get("retrievable", False)

        capability_resources = kwargs.get("capability_resources", None)
        if capability_resources:
            capability["capabilityResources"] = capability_resources

        configuration_range = kwargs.get("configuration_range", None)
        if configuration_range:
            capability["configuration"] = {}
            capability["configuration"]["supportedRange"] = configuration_range
            capability["configuration"]["presets"] = kwargs.get("presets", [])
            capability["configuration"]["unitOfMeasure"] = kwargs.get("unit_of_measure", None)

        configuration_modes = kwargs.get("configuration_modes", None)
        if configuration_modes:
            capability["configuration"] = {}
            capability["configuration"]["supportedModes"] = configuration_modes

        configuration_measurement = kwargs.get("configuration_measurement", None)
        configuration_replenishment = kwargs.get("configuration_replenishment", None)
        if configuration_measurement:
            capability["configuration"] = {}
            capability["configuration"]["measurement"] = configuration_measurement
            if configuration_replenishment:
                capability["configuration"]["replenishment"] = configuration_replenishment

        configuration_ordered = kwargs.get("configuration_ordered", None)
        if configuration_ordered is not None:
            capability["configuration"]["ordered"] = configuration_ordered

        verifications_required = kwargs.get("verifications_required", None)
        if verifications_required:
          capability["verificationsRequired"] = []
          for directive in verifications_required:
            capability["verificationsRequired"].append({"directive": directive, "methods": [{"@type": "Confirmation"}]})

        semantics_actions = kwargs.get("semantics_actions", None)
        if semantics_actions:
            capability["semantics"] = {}
            capability["semantics"]["actionMappings"] = semantics_actions

        semantics_states = kwargs.get("semantics_states", None)
        if semantics_states:
            capability["semantics"]["stateMappings"] = semantics_states

        return capability

    def get(self, remove_empty=True):

        response = {
            "context": self.context,
            "event": self.event
        }

        if len(self.context_properties) > 0:
            response["context"]["properties"] = self.context_properties

        if len(self.payload_endpoints) > 0:
            response["event"]["payload"]["endpoints"] = self.payload_endpoints

        if len(self.payload_properties) > 0:
            response["event"]["payload"]["change"] = {
                "cause": {"type": "PHYSICAL_INTERACTION"},
                "properties": self.payload_properties
            }

        if self.payload_timestamp:
            response["event"]["payload"]["cause"] = {"type": "PHYSICAL_INTERACTION"}
            response["event"]["payload"]["timestamp"] = self.payload_timestamp

        if remove_empty:
            if len(response["context"]) < 1:
                response.pop("context")

        return response

    def set_payload(self, payload):
        self.event["payload"] = payload

    def set_payload_endpoint(self, payload_endpoints):
        self.payload_endpoints = payload_endpoints

    def set_payload_endpoints(self, payload_endpoints):
        if "endpoints" not in self.event["payload"]:
            self.event["payload"]["endpoints"] = []

        self.event["payload"]["endpoints"] = payload_endpoints
