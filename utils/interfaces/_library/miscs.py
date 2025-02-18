# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

""" Misc validations """

from collections import Counter

from utils.interfaces._core import BaseValidation
from utils.interfaces._library._utils import get_root_spans, _get_rid_from_span


class _TraceIdUniqueness(BaseValidation):
    path_filters = r"/v[0-9]\.[0-9]+/traces"  # Should be implemented independently from the endpoint version

    is_success_on_expiry = False  # I need at least one value to be validated

    def __init__(self, uniqueness_exceptions):
        super().__init__()
        self.traces_ids = Counter()
        self.uniqueness_exceptions = uniqueness_exceptions

    def check(self, data):
        for trace in data["request"]["content"]:
            if len(trace):
                span = trace[0]
                self.is_success_on_expiry = True

                if "trace_id" not in span:
                    self.set_failure(f"Can't find trace_id in request number {data['log_filename']}")
                else:
                    trace_id = span["trace_id"]
                    self.traces_ids[trace_id] += 1

    def final_check(self):
        for trace_id, count in self.traces_ids.items():
            if count > 1 and self.uniqueness_exceptions.should_be_unique(trace_id):
                self.log_error(f"Found duplicate trace id {trace_id}")


class _ReceiveRequestRootTrace(BaseValidation):
    """Asserts that a trace for a request has been sent to the agent"""

    path_filters = ["/v0.4/traces"]
    is_success_on_expiry = False

    def check(self, data):
        for root_span in get_root_spans(data["request"]["content"]):
            if root_span.get("type") != "web":
                continue
            self.set_status(True)

    def set_expired(self):
        super().set_expired()
        if not self.is_success:
            self.log_error(
                f'Validation "{self.message}", nothing has been reported. No request root span with has been found'
            )


class _SpanValidation(BaseValidation):
    """ will run an arbitrary check on spans. If a request is provided, only span
        related to this request will be checked.

        Validator function can :
        * returns true => validation will be validated at the end (but trace will continue to be checked)
        * returns False or None => nothing is done
        * raise an exception => validation will fail
    """

    path_filters = "/v0.4/traces"

    def __init__(self, request, validator):
        super().__init__(request=request)
        self.validator = validator

    def check(self, data):
        for trace in data["request"]["content"]:
            for span in trace:
                if self.rid:
                    if self.rid != _get_rid_from_span(span):
                        continue
                    else:
                        self.log_debug(f"Found a trace for {self.message}")

                try:
                    if self.validator(span):
                        self.is_success_on_expiry = True
                except Exception as e:
                    self.set_failure(f"{self.message} not validated: {e}\nSpan is: {span}")
