"""Verify an already-deployed demo without credentials or real store writes."""
import sys
import time
import httpx


def verify(base_url):
    with httpx.Client(base_url=base_url, timeout=90, follow_redirects=True) as browser:
        health = browser.get('/api/health')
        health.raise_for_status()
        info = health.json()
        assert info['demo_mode'] is True, 'Only run this smoke check against demo mode'
        assert info['storage'] == 'private-blob-and-redis'
        print('Cloud health and demo mode verified', flush=True)
        for path in ('/', '/create', '/bulk', '/history', '/settings', '/impact', '/under-the-hood'):
            response = browser.get(path)
            assert response.status_code == 200, (path, response.status_code)
        print('All seven pages return 200', flush=True)
        created = browser.post('/api/jobs/sample', json={'sample':'bottle','style':'shadow','language':'en'})
        assert created.status_code == 202, created.text
        identifier = created.json()['id']
        endpoint = '/api/jobs/'+identifier
        deadline = time.monotonic()+120
        observed = None
        while time.monotonic() < deadline:
            response = browser.get(endpoint)
            response.raise_for_status()
            job = response.json()
            progress = tuple(stage['status'] for stage in job['stages'])
            if observed != progress:
                print('Stages: '+', '.join(progress), flush=True)
                observed = progress
            if job['status'] == 'ready': break
            assert job['status'] not in {'failed','cancelled'}, job.get('error')
            time.sleep(1)
        else: raise AssertionError('Cloud processing did not finish within 120 seconds')
        assert all(stage['status']=='completed' for stage in job['stages'])
        for media in (job['source_images'][0], job['result']['variants']['shadow']):
            response = browser.get(media)
            assert response.status_code == 200 and len(response.content)>1000
        with httpx.Client(base_url=base_url, timeout=30) as stranger:
            assert stranger.get('/api/jobs').json() == []
            assert stranger.get(endpoint).status_code == 404
            assert stranger.get(job['source_images'][0]).status_code == 404
        print('Private images and visitor isolation verified', flush=True)
        edit = browser.patch(endpoint, json={
            'copy':{**job['result']['copy'],'title':'Cloud smoke-test bottle'},
            'final_price':875.5, 'language':'en', 'selected_style':'shadow',
        })
        edit.raise_for_status()
        edited = edit.json()
        payload = browser.get(endpoint+'/payload').json()
        assert payload['product']['title']=='Cloud smoke-test bottle'
        assert payload['variant']['price']=='875.50'
        assert browser.post(endpoint+'/publish',json={'approved':False,'channel':'shopify','revision':edited['revision']}).status_code == 422
        body={'approved':True,'channel':'shopify','revision':edited['revision']}
        synced = browser.post(endpoint+'/publish',json=body)
        synced.raise_for_status()
        result = synced.json()
        assert result['store_result']['demo'] is True and result['store_result']['status']=='draft'
        assert browser.post(endpoint+'/publish',json=body).json()['store_result']['id']==result['store_result']['id']
        with httpx.Client(base_url=base_url, timeout=30, cookies=browser.cookies) as returning:
            saved = returning.get(endpoint).json()
            assert saved['status']=='published'
            assert saved['result']['copy']['title']=='Cloud smoke-test bottle'
            assert saved['result']['final_price']==875.5
        settings = browser.get('/api/settings').json()
        assert settings['settings_readonly'] is True
        print(f'PASS: six stages, private media, saved edits, approved demo draft, idempotency and returning visitor ({identifier})', flush=True)


if __name__ == '__main__':
    if len(sys.argv)!=2 or not sys.argv[1].startswith('https://'):
        raise SystemExit('Usage: python -m backend.scripts.smoke_cloud https://your-app.vercel.app')
    verify(sys.argv[1].rstrip('/'))
