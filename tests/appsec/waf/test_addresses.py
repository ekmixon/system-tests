# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.


from utils import context, BaseTestCase, interfaces, released, bug, irrelevant, missing_feature
import pytest


if context.weblog_variant == "echo-poc":
    pytestmark = pytest.mark.skip("not relevant: echo is not instrumented")
elif context.library == "cpp":
    pytestmark = pytest.mark.skip("not relevant")


@released(golang="?", dotnet="?", java="?", php="?", python="?", ruby="?")
@missing_feature(library="nodejs", reason="query string not yet supported")
class Test_UrlQueryKey(BaseTestCase):
    """Appsec supports keys on server.request.query"""

    def test_query_key(self):
        """ AppSec catches attacks in URL query key"""
        r = self.weblog_get("/waf/", params={"appscan_fingerprint": "attack"})
        interfaces.library.assert_waf_attack(r, pattern="appscan_fingerprint", address="server.request.query")

    def test_query_key_encoded(self):
        """ AppSec catches attacks in URL query key"""
        r = self.weblog_get("/waf/", params={"<script>": "attack"})
        interfaces.library.assert_waf_attack(r, pattern="<script>", address="server.request.query")


@released(golang="1.33.1", dotnet="1.28.6", java="0.87.0", nodejs="?", php="?", python="?", ruby="?")
class Test_UrlQuery(BaseTestCase):
    """Appsec supports values on server.request.query"""

    def test_query_argument(self):
        """ AppSec catches attacks in URL query value"""
        r = self.weblog_get("/waf/", params={"attack": "appscan_fingerprint"})
        interfaces.library.assert_waf_attack(r, pattern="appscan_fingerprint", address="server.request.query")

    @bug(library="golang")
    @irrelevant(context.waf_rule_set >= "1.0.0", reason="Rules set 1.0.0 => libxss does not report highlight")
    def test_query_encoded_legacy(self):
        """ AppSec catches attacks in URL query value, even encoded"""
        r = self.weblog_get("/waf/", params={"key": "<script>"})
        interfaces.library.assert_waf_attack(r, pattern="<script>", address="server.request.query")

    @bug(library="golang")
    def test_query_encoded(self):
        """ AppSec catches attacks in URL query value, even encoded"""
        r = self.weblog_get("/waf/", params={"key": "<script>"})
        interfaces.library.assert_waf_attack(r, address="server.request.query")

    def test_query_with_strict_regex(self):
        """ AppSec catches attacks in URL query value, even with regex containing"""
        r = self.weblog_get("/waf/", params={"value": "0000012345"})
        interfaces.library.assert_waf_attack(r, pattern="0000012345", address="server.request.query")


@released(golang="1.33.1", dotnet="1.28.6", java="0.87.0")
@released(nodejs="2.0.0-appsec-alpha.1", php="?", python="?", ruby="0.51.0")
class Test_UrlRaw(BaseTestCase):
    """Appsec supports server.request.uri.raw"""

    def test_path(self):
        """ AppSec catches attacks in URL path"""
        r = self.weblog_get("/waf/0x5c0x2e0x2e0x2f")
        interfaces.library.assert_waf_attack(r, pattern="0x5c0x2e0x2e0x2f", address="server.request.uri.raw")


@released(golang="1.33.1", dotnet="1.28.6", java="0.87.0")
@released(nodejs="2.0.0-appsec-alpha.1", php="?", python="?", ruby="0.51.0")
class Test_Headers(BaseTestCase):
    """Appsec supports server.request.headers.no_cookies"""

    def test_value(self):
        """ Appsec WAF detects attacks in header value """
        r = self.weblog_get("/waf/", headers={"User-Agent": "Arachni/v1"})
        interfaces.library.assert_waf_attack(
            r, pattern="Arachni/v", address="server.request.headers.no_cookies", key_path=["user-agent"]
        )

    def test_specific_key(self):
        """ Appsec WAF detects attacks on specific header x-file-name or referer, and report it """
        r = self.weblog_get("/waf/", headers={"x-file-name": "routing.yml"})
        interfaces.library.assert_waf_attack(
            r, pattern="routing.yml", address="server.request.headers.no_cookies", key_path=["x-file-name"]
        )

        r = self.weblog_get("/waf/", headers={"X-File-Name": "routing.yml"})
        interfaces.library.assert_waf_attack(
            r, pattern="routing.yml", address="server.request.headers.no_cookies", key_path=["x-file-name"]
        )

        r = self.weblog_get("/waf/", headers={"X-Filename": "routing.yml"})
        interfaces.library.assert_waf_attack(
            r, pattern="routing.yml", address="server.request.headers.no_cookies", key_path=["x-filename"]
        )

    @irrelevant(library="ruby", reason="Rack transforms undersocre to dashes")
    def test_specific_key2(self):
        """ attacks on specific header X_Filename, and report it """
        r = self.weblog_get("/waf/", headers={"X_Filename": "routing.yml"})
        interfaces.library.assert_waf_attack(
            r, pattern="routing.yml", address="server.request.headers.no_cookies", key_path=["x_filename"]
        )

    @irrelevant(context.waf_rule_set >= "1.0.0", reason="Rules set 1.0.0 => libxss does not report highlight")
    @bug(library="golang", reason="entire address is missing")
    def test_specific_key3_legacy(self):
        """ When a specific header key is specified, other key are ignored """
        r = self.weblog_get("/waf/", headers={"referer": "<script >"})
        interfaces.library.assert_waf_attack(
            r, pattern="<script >", address="server.request.headers.no_cookies", key_path=["referer"]
        )

        r = self.weblog_get("/waf/", headers={"RefErEr": "<script >"})
        interfaces.library.assert_waf_attack(
            r, pattern="<script >", address="server.request.headers.no_cookies", key_path=["referer"]
        )

    def test_specific_key3(self):
        """ When a specific header key is specified, other key are ignored """
        r = self.weblog_get("/waf/", headers={"referer": "<script >"})
        interfaces.library.assert_waf_attack(r, address="server.request.headers.no_cookies", key_path=["referer"])

        r = self.weblog_get("/waf/", headers={"RefErEr": "<script >"})
        interfaces.library.assert_waf_attack(r, address="server.request.headers.no_cookies", key_path=["referer"])

    def test_specific_wrong_key(self):
        """ When a specific header key is specified in rules, other key are ignored """
        r = self.weblog_get("/waf/", headers={"xfilename": "routing.yml"})
        interfaces.library.assert_no_appsec_event(r)

        r = self.weblog_get("/waf/", headers={"not-referer": "<script >"})
        interfaces.library.assert_no_appsec_event(r)


@released(golang="1.33.1", php="?", python="?", ruby="0.51.0")
@missing_feature(library="nodejs", reason="cookies not yet supported?")
class Test_Cookies(BaseTestCase):
    """Appsec supports server.request.cookies"""

    def test_cookies(self):
        """ Appsec WAF detects attackes in cookies """
        r = self.weblog_get("/waf/", cookies={"attack": ".htaccess"})
        interfaces.library.assert_waf_attack(r, pattern=".htaccess", address="server.request.cookies")

    @bug(library="dotnet", reason="APPSEC-1407 and APPSEC-1408")
    @bug(library="java", reason="under Valentin's investigations")
    @bug(library="golang")
    @bug(library="ruby")
    def test_cookies_with_special_chars(self):
        """Other cookies patterns, to be merged once issue are corrected"""
        r = self.weblog_get("/waf", cookies={"value": ";shutdown--"})
        interfaces.library.assert_waf_attack(r, pattern=";shutdown--", address="server.request.cookies")

        r = self.weblog_get("/waf", cookies={"key": ".cookie-;domain="})
        interfaces.library.assert_waf_attack(r, pattern=".cookie-;domain=", address="server.request.cookies")

        r = self.weblog_get("/waf/", cookies={"x-attack": " var_dump ()"})
        interfaces.library.assert_waf_attack(r, pattern=" var_dump ()", address="server.request.cookies")

    @bug(library="dotnet", reason="APPSEC-1407 and APPSEC-1408")
    @bug(library="java", reason="under Valentin's investigations")
    @bug(library="golang")
    def test_cookies_with_special_chars2(self):
        """Other cookies patterns, to be merged once issue are corrected"""
        r = self.weblog_get("/waf/", cookies={"x-attack": 'o:4:"x":5:{d}'})
        interfaces.library.assert_waf_attack(r, pattern='o:4:"x":5:{d}', address="server.request.cookies")


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
class Test_BodyRaw(BaseTestCase):
    """Appsec supports <body>"""

    @missing_feature(True, reason="no rule with body raw yet")
    def test_raw_body(self):
        """AppSec detects attacks in raw body"""
        r = self.weblog_post("/waf", data="/.adsensepostnottherenonobook")
        interfaces.library.assert_waf_attack(r, pattern="x", address="x")


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
class Test_BodyUrlEncoded(BaseTestCase):
    """Appsec supports <url encoded body>"""

    @missing_feature(library="java")
    def test_body_key(self):
        """AppSec detects attacks in URL encoded body keys"""
        r = self.weblog_post("/waf", data={'<vmlframe src="xss">': "value"})
        interfaces.library.assert_waf_attack(r, pattern="x", address="x")

    @missing_feature(library="java")
    def test_body_value(self):
        """AppSec detects attacks in URL encoded body values"""
        r = self.weblog_post("/waf", data={"value": '<vmlframe src="xss">'})
        interfaces.library.assert_waf_attack(r, pattern="x", address="x")


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
class Test_BodyJson(BaseTestCase):
    """Appsec supports <JSON encoded body>"""

    def test_json_key(self):
        raise NotImplementedError()

    def test_json_value(self):
        raise NotImplementedError()

    def test_json_array(self):
        raise NotImplementedError()


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
class Test_BodyXml(BaseTestCase):
    """Appsec supports <XML encoded body>"""

    def test_xml_node(self):
        raise NotImplementedError()

    def test_xml_attr(self):
        raise NotImplementedError()

    def test_xml_attr_value(self):
        raise NotImplementedError()

    def test_xml_content(self):
        raise NotImplementedError()


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
@irrelevant(library="nodejs", reason="not yet rule on method")
class Test_Method(BaseTestCase):
    """Appsec supports server.request.method"""

    def test_method(self):
        raise NotImplementedError


@released(golang="?", dotnet="?", java="?", nodejs="?", php="?", python="?", ruby="?")
@irrelevant(library="nodejs", reason="not yet rule on client_ip")
class Test_ClientIP(BaseTestCase):
    """Appsec supports server.request.client_ip"""

    def test_client_ip(self):
        """ Appsec WAF supports server.request.client_ip """
        raise NotImplementedError
