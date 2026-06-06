import dashscope
from http import HTTPStatus

dashscope.api_key = "sk-ws-H.HLXLMP.bsb6.MEUCIQDGgGDCO-IC4PgfH3-M_zdsFm3vWz7z9sL9Eb99c4keQIgDgWfWhyQwFh3gYngwdr_P82ItOMgnm_Mz38U2_jgJdQ"
dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

resp = dashscope.TextEmbedding.call(
    model="text-embedding-v4",
    input="The quality of the clothes is excellent"
)
print(resp)
