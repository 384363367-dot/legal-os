"""Public source-specific endpoint and category metadata.

The values in this module are routing metadata for official pages and public
interfaces.  It deliberately contains no downloaded source content.
"""
from __future__ import annotations

from urllib.parse import urljoin


NPC_BASE = "https://flk.npc.gov.cn"
GOV_RULES_INDEX = "https://www.gov.cn/zhengce/xxgk/gjgzk/index.htm?searchWord="
GOV_RULES_QUERY_PATH = "/athena/forward/BD8730CDDA12515E2D9E1B21AA11C0D6"
TREATY_BASE = "https://treaty.mfa.gov.cn/web/"
MOJ_SEARCH_URL = "https://xzfg.moj.gov.cn/search2.html"
PARTY_BASE = "https://www.12371.cn/special/dnfg"
MOD_BASE = "https://www.mod.gov.cn/gfbw/fgwx"
TAX_BASE = "https://fgk.chinatax.gov.cn"
TAX_API = "https://www.chinatax.gov.cn/getFileListByCodeId"
MEE_BASE = "https://www.mee.gov.cn/ywgz/fgbz"
SPC_BASE = "https://www.court.gov.cn"


CATEGORY_MAPS: dict[str, dict[str, str]] = {
    "gov-rules": {"部门规章": "部门规章", "地方政府规章": "地方政府规章"},
    "mfa-treaty": {"全部": "allinfos.jsp", "双边": "shuangbian.jsp", "多边": "duobian.jsp"},
    "state-council-policy": {"全部": "", "国务院文件": "gongwen", "国务院部门文件": "bumenfile", "解读": "otherfile"},
    "party-rules": {
        "全部": "",
        "党章": "zz",
        "条例": "tl",
        "规定": "gd",
        "办法": "bf",
        "规则": "gz",
        "细则": "xz",
        "党的组织法规": "zzfg",
        "党的领导法规": "ldfg",
        "党的自身建设法规": "zsjs",
        "党的监督保障法规": "jdbz",
    },
    "mod-regulations": {
        "全部": "",
        "法律法规": "flfg",
        "白皮书": "bps",
        "文件": "wj_213958",
        "司法解释": "sfjs",
        "出版物": "cbw",
        "热点聚焦": "rdjj_213961",
        "政策解读": "zcjd",
    },
    "tax-rules": {
        "全部": "",
        "法律": "c100009",
        "行政法规": "c100010",
        "国务院文件": "c102440",
        "税务部门规章": "c100011",
        "财税文件": "c102416",
        "税务规范性文件": "c100012",
        "其他文件": "c100013",
        "工作通知": "c102424",
    },
    "mee-regulations": {
        "全部": "",
        "法律": "fl",
        "行政法规": "xzfg",
        "规章": "gz",
        "生态环境损害赔偿制度": "sthjshpczd",
        "行政复议与执法解释": "zfjs",
    },
    "spc-publications": {
        "全部": "",
        "司法解释": "16",
        "司法文件": "17",
        "重大案件": "15",
        "通知": "22",
        "司法数据": "21",
        "大数据专题": "662",
        "标准化工作": "108",
        "任免招录": "79",
        "开庭公告": "14",
    },
}


def category_options(source_id: str) -> tuple[str, ...]:
    return tuple(CATEGORY_MAPS.get(source_id, {}))


def category_code(source_id: str, label: str | None) -> str:
    if not label:
        return ""
    return CATEGORY_MAPS.get(source_id, {}).get(label, label)


def treaty_list_url(category: str, page: int = 1) -> str:
    path = CATEGORY_MAPS["mfa-treaty"].get(category, "allinfos.jsp")
    return urljoin(TREATY_BASE, f"{path}?nPageIndex_={max(1, page)}")


def party_list_url(category_code_value: str, page: int = 1) -> str:
    suffix = f"/{category_code_value}" if category_code_value else ""
    url = f"{PARTY_BASE}{suffix}/"
    return url if page <= 1 else f"{url}?page={page}"


def mod_list_url(category_code_value: str, page: int = 1) -> str:
    suffix = f"/{category_code_value}" if category_code_value else ""
    base = f"{MOD_BASE}{suffix}/index.html"
    return base if page <= 1 else f"{MOD_BASE}{suffix}/index_{page}.html"


def mee_list_url(category_code_value: str) -> str:
    if category_code_value == "gz":
        return "https://www.mee.gov.cn/gzk/gz/"
    return f"{MEE_BASE}/{category_code_value}/" if category_code_value else f"{MEE_BASE}/"


def spc_list_url(category_code_value: str, page: int = 1) -> str:
    category_code_value = category_code_value or "16"
    path = f"/fabu/gengduo/{category_code_value}.html"
    if page > 1:
        path = f"/fabu/gengduo/{category_code_value}_{page}.html"
    return f"{SPC_BASE}{path}"


def tax_category_url(code_name: str, variant: str = "listflfg.html") -> str:
    return f"{TAX_BASE}/zcfgk/{code_name}/{variant}"


def category_label(source_id: str, code: str) -> str:
    for label, value in CATEGORY_MAPS.get(source_id, {}).items():
        if value == code:
            return label
    return code
