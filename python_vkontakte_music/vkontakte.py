import requests
from http import cookiejar as cookielib
import urllib.request as urllib2
from urllib.parse import urlparse, urlencode
from html.parser import HTMLParser


class VkontakteError(Exception):
    def __init__(self, error):
        super(VkontakteError, self).__init__(error)
        self.error = error
        self.error_code = int(error['error_code'])
        self.error_msg = str(error['error_msg'])
        self.request_params = error['request_params']


class VkontakteClient:
    api_version = '5.34'

    def __init__(self, access_token=None, api_version=None):
        self.access_token = access_token
        if api_version is not None:
            self.api_version = api_version

    def _compile_params(self, params_dict):
        params = list()
        for key in params_dict:
            if params_dict[key]:
                if isinstance(params_dict[key], list):
                    params.append((key, ','.join(map(str, params_dict[key]))))
                else:
                    params.append((key, str(params_dict[key])))
        if self.access_token:
            params.append(("access_token", str(self.access_token)))
        params.append(('v', str(self.api_version)))
        return params

    @classmethod
    def auth(cls, email, password, application_id, scope):
        access_token = auth(email, password, application_id, scope)[0]
        return cls(access_token)

    def call(self, method, **params_dict):
        params = self._compile_params(params_dict)
        url = 'https://api.vk.com/method/{}?{}'.format(method, urlencode(params))
        response = requests.get(url).json()
        if 'error' in response:
            raise VkontakteError(response['error'])
        return response['response']


class _FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise ValueError("Second form on page")
            if self.in_form:
                raise ValueError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True


def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    # Authorization form
    def auth_user(email, password, client_id, scope, opener):
        response = opener.open(
            "http://oauth.vk.com/oauth/authorize?" + \
            "redirect_uri=http://oauth.vk.com/blank.html&response_type=token&" + \
            "client_id=%s&scope=%s&display=wap" % (client_id, ",".join(scope))
            )
        doc = response.read().decode()
        parser = _FormParser()
        parser.feed(doc)
        parser.close()
        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or \
          "email" not in parser.params:
              raise ValueError("Something wrong")
        parser.params["email"] = email
        parser.params["pass"] = password
        if parser.method == "POST":
            response = opener.open(parser.url, urlencode(parser.params).encode())
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.read(), response.geturl()

    # Permission request form
    def give_access(doc, opener):
        parser = _FormParser()
        parser.feed(doc)
        parser.close()
        if not parser.form_parsed or parser.url is None:
              raise ValueError("Something wrong")
        if parser.method == "POST":
            response = opener.open(parser.url, urlencode(parser.params))
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.geturl()

    if not isinstance(scope, list):
        scope = [scope]
    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib2.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)
    if urlparse(url).path != "/blank.html":
        raise ValueError("Expected success here")
    answer = dict(split_key_value(kv_pair) for kv_pair in urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise ValueError("Missing some values in answer")
    return answer["access_token"], answer["user_id"], answer["expires_in"]


