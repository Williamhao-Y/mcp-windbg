import re


# 电子邮件
EMAIL = re.compile(
    r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    re.IGNORECASE,
)

# Authorization: Bearer ...
BEARER_TOKEN = re.compile(
    r"(?i)\b(authorization\s*:\s*bearer\s+)[^\s,;]+"
)

# JWT
JWT = re.compile(
    r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
)

# 常见的 key=value 秘密
KEY_VALUE_SECRET = re.compile(
    r"""(?ix)
    \b(
        api[_-]?key
        |access[_-]?token
        |refresh[_-]?token
        |client[_-]?secret
        |password
        |passwd
        |pwd
    )
    \s*[:=]\s*
    (?:
        "[^"]*"
        |'[^']*'
        |[^\s,;]+
    )
    """
)


# KDNET 示例：net:port=50000,key=1.2.3.4
KDNET_KEY = re.compile(
    r"(?i)(\bkey\s*=\s*)[A-Za-z0-9.-]+"
)


def redact(text):
    """对一段纯文本应用所有脱敏规则。"""
    text = EMAIL.sub("[REDACTED_EMAIL]", text)
    text = BEARER_TOKEN.sub(r"\1[REDACTED_TOKEN]", text)
    text = JWT.sub("[REDACTED_JWT]", text)
    text = KEY_VALUE_SECRET.sub(
        lambda match: f"{match.group(1)}=[REDACTED_SECRET]",
        text,
    )
    text = WINDOWS_USER_PATH.sub(r"C:\\Users\\[REDACTED_USER]", text)
    text = KDNET_KEY.sub(r"\1[REDACTED_KDNET_KEY]", text)
    return text


def process_output(text, context):
    """
    清洗工具返回结果。

    这是最重要的回调，因为调试器输出会在这里经过处理，
    然后才返回 MCP 客户端。
    """
    return redact(text)


def process_input(text, context):
    """
    可选：处理客户端传给工具的字符串参数。

    注意：修改 dump_path、connection_string 或 WinDbg 命令可能改变
    工具实际执行的内容，因此这里仅演示按参数位置选择性处理。
    """
    if (
        context["tool_name"] in {"run_cdb_command", "run_kd_command"}
        and context.get("argument_path") == "$.command"
    ):
        return redact(text)

    return text