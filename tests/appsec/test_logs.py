# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import BaseTestCase, context, interfaces, released, irrelevant, missing_feature, bug
import pytest


if context.weblog_variant == "echo-poc":
    pytestmark = pytest.mark.skip("not relevant: echo is not instrumented")
elif context.library == "cpp":
    pytestmark = pytest.mark.skip("not relevant")

# get the default log output
stdout = interfaces.library_stdout if context.library != "dotnet" else interfaces.library_dotnet_managed


@released(golang="?", nodejs="?", php="?", python="?", ruby="?")
class Test_Standardization(BaseTestCase):
    """AppSec logs should be standardized"""

    @classmethod
    def setup_class(cls):
        """Send a bunch of attack, to be sure that something is done on AppSec side"""
        get = cls().weblog_get

        get("/waf", params={"key": "\n :"})  # rules.http_protocol_violation.crs_921_160
        get("/waf", headers={"random-key": "acunetix-user-agreement"})  # rules.security_scanner.crs_913_110

    @irrelevant(library="java", reason="Cannot be implemented with cooperation from libddwaf")
    def test_d01(self):
        """Log D1: names and adresses AppSec listen to"""
        stdout.assert_presence(r"Loaded rule:", level="DEBUG")  # TODO: should be more precise

    @missing_feature(library="dotnet")
    @irrelevant(library="java", reason="IG doesn't push addresses in Java.")
    def test_d02(self):
        """Log D2: Address pushed to Instrumentation Gateway"""
        stdout.assert_presence(r"Pushing address .* to the Instrumentation Gateway.", level="DEBUG")

    @missing_feature(library="dotnet")
    @missing_feature(library="java")
    def test_d03(self):
        """Log D3: When an address matches a rule needs"""
        stdout.assert_presence(r"Available addresses .* match needs for rules", level="DEBUG")

    @missing_feature(library="dotnet")
    @missing_feature(library="java")
    def test_d04(self):
        """Log D4: When calling the WAF, logs parameters"""
        stdout.assert_presence(r"Executing AppSec In-App WAF with parameters:", level="DEBUG")

    @bug(context.library == "java@0.90.0", reason="APPSEC-2190")
    @bug(context.library == "java@0.91.0", reason="APPSEC-2190")
    @missing_feature(library="dotnet")
    def test_d05(self):
        """Log D5: WAF outputs"""
        stdout.assert_presence(r'AppSec In-App WAF returned:.*"rule":"crs-921-160"', level="DEBUG")
        stdout.assert_presence(r'AppSec In-App WAF returned:.*"rule":"crs-913-110"', level="DEBUG")

    @missing_feature(library="dotnet")
    def test_d06(self):
        """Log D6: WAF rule detected an attack with details"""
        stdout.assert_presence(r"Detecting an attack from rule crs-921-160:.*", level="DEBUG")
        stdout.assert_presence(r"Detecting an attack from rule crs-913-110:.*", level="DEBUG")

    @missing_feature(True, reason="not testable as now")
    def test_d07(self):
        """Log D7: Exception in rule"""
        stdout.assert_presence(r"Rule .* failed. Error details: ", level="DEBUG")

    @missing_feature(library="dotnet")
    def test_d09(self):
        """Log D9: WAF start of execution"""
        stdout.assert_presence(r"Executing AppSec In-App WAF$", level="DEBUG")

    @missing_feature(library="dotnet")
    def test_d10(self):
        """Log D10: WAF end of execution"""
        stdout.assert_presence(r"Executing AppSec In-App WAF finished. Took \d+ ms\.$", level="DEBUG")

    @missing_feature(library="dotnet")
    def test_i01(self):
        """Log I1: AppSec initial configuration"""
        stdout.assert_presence(r"AppSec initial configuration from .*, libddwaf version: \d+\.\d+\.\d+", level="INFO")

    @missing_feature(library="dotnet")
    def test_i02(self):
        """Log I2: AppSec rule source"""
        stdout.assert_presence(r"AppSec loaded \d+ rules from file .*$", level="INFO")

    @missing_feature(library="dotnet")
    @missing_feature(context.library <= "java@0.88.0", reason="small typo")
    def test_i05(self):
        """Log I5: WAF detected an attack"""
        stdout.assert_presence(r"Detecting an attack from rule crs-921-160$", level="INFO")
        stdout.assert_presence(r"Detecting an attack from rule crs-913-110$", level="INFO")

    @missing_feature(library="dotnet")
    def test_i07(self):
        """Log I7: Pushing AppSec events"""
        stdout.assert_presence(r"Pushing new attack to AppSec events$", level="INFO")

    @missing_feature(library="dotnet")
    def test_i08(self):
        """Log I8: Sending AppSec events"""
        stdout.assert_presence(r"Sending \d+ AppSec events to the agent$", level="INFO")

    @missing_feature(True, reason="not testable as now")
    def test_i09(self):
        """Log I9: Dropping events"""
        stdout.assert_presence(r"Dropping \d+ AppSec events because ", level="INFO")

    @missing_feature(True, reason="not testable as now")
    def test_i10(self):
        """Log I10: Flushing events before shutdown"""
        stdout.assert_presence(r"Reporting AppSec event batch because of process shutdown.$", level="INFO")


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
class Test_StandardizationBlockMode(BaseTestCase):
    """AppSec blocking logs should be standardized"""

    @classmethod
    def setup_class(cls):
        """Send a bunch of attack, to be sure that something is done on AppSec side"""
        get = cls().weblog_get

        get("/waf", params={"key": "\n :"})  # rules.http_protocol_violation.crs_921_160
        get("/waf", headers={"random-key": "acunetix-user-agreement"})  # rules.security_scanner.crs_913_110

    def test_i06(self):
        """Log I6: AppSec blocked a request"""
        stdout.assert_presence(r"Blocking current transaction \(rule: .*\)$", level="INFO")
