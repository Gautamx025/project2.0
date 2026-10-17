import io
import json
from pathlib import Path
import httpx
import pytest
from PIL import Image
from backend.app import adapters, config
from backend.app.adapters import Background, Price, Segmentation, Vision
from backend.app.demo import demo_vision

@pytest.mark.parametrize('provider',['gemini','openai'])
async def test_vision_live_request_and_strict_response(provider,monkeypatch):
    expected=demo_vision('bottle').model_dump()
    async def handler(request):
        body=json.loads(request.content)
        if provider=='gemini':
            assert body['contents'][0]['parts'][1]['inlineData']['mimeType']=='image/jpeg'
            assert body['generationConfig']['responseFormat']['text']['schema']['additionalProperties'] is False
            text=json.dumps(expected)
            return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':text[:80]},{'text':text[80:]}]}}]})
        assert body['model']=='gpt-4o'
        assert body['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
        assert body['response_format']['json_schema']['strict'] is True
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(expected)}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters,'client',lambda:http)
        actual=await Vision(provider).live([config.ROOT/'frontend/public/samples/bottle.jpg'],'bottle')
    assert actual.title=='Steel water bottle' and actual.marathi.title=='स्टीलची पाण्याची बाटली'

async def test_fal_sam_and_flux_image_contracts(isolated_environment,monkeypatch):
    image=io.BytesIO();Image.new('RGBA',(100,100),(255,0,0,150)).save(image,format='PNG')
    seen=[]
    async def handler(request):
        seen.append(str(request.url))
        if request.method=='GET':return httpx.Response(200,content=image.getvalue())
        body=json.loads(request.content)
        assert body['image_url'].startswith('data:image/')
        if 'sam' in request.url.path:
            assert body['apply_mask'] is True and body['prompts'][0]['label']==1
            return httpx.Response(200,json={'image':{'url':'https://assets.example/cutout.png'}})
        assert 'Preserve the exact product' in body['prompt']
        return httpx.Response(200,json={'images':[{'url':'https://assets.example/studio.png'}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters,'client',lambda:http)
        source=config.ROOT/'frontend/public/samples/bottle.jpg'
        cutout=Path(await Segmentation('fal').live(source,isolated_environment.media/'cutout.png'))
        result=Path(await Background('fal').live(cutout,isolated_environment.media/'studio.png','studio'))
    assert cutout.exists() and result.exists() and len(seen)==4
    assert Image.open(cutout).getpixel((0,0))[3]==150

async def test_serpapi_links_and_currency_are_retained(isolated_environment,monkeypatch):
    async def handler(request):
        assert request.url.params['engine']=='google_shopping' and request.url.params['gl']=='in'
        return httpx.Response(200,json={'shopping_results':[{'title':'A','product_link':'https://a.example/product','price':'₹400'},{'title':'B','link':'https://b.example/product','price':'Rs. 800'},{'title':'Wrong currency','link':'https://c.example','price':'$90'}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters,'client',lambda:http)
        result=await Price('serpapi',isolated_environment).live('test product','custom')
    assert result.median==600 and [source.url for source in result.sources]==['https://a.example/product','https://b.example/product']
