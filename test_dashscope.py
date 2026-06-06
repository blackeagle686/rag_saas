import dashscope

dashscope.api_key = "sk-ws-H.HLXLMP.bsb6.MEUCIQDGgGDCO-IC4PgfH3-M_zdsFm3vWz7z9sL9Eb99c4keQIgDgWfWhyQwFh3gYngwdr_P82ItOMgnm_Mz38U2_jgJdQ"

resp = dashscope.TextEmbedding.call(
    model="text-embedding-v4",
    input="The quality of the clothes is excellent"
)
print(resp)
