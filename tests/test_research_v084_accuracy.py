"""Synthetic contract tests for the independent public adapters (no live requests)."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/cn-legal-research/scripts'))
import download
import article_search
import site_adapters
from research_runtime import SourceResponse,SourceAccessError

class Client:
    def __init__(self,payload=None,html=None):self.payload=payload;self.html=html;self.calls=[]
    def request(self,method,url,**kwargs):
        self.calls.append((method,url,kwargs))
        body=self.html.encode() if self.html is not None else json.dumps(self.payload).encode()
        return SourceResponse(200,url,{'content-type':'text/html' if self.html is not None else 'application/json'},body)

def page(query='示例条例ZVING1',title='示例条例',count=1,detail_url='/front/law/detail?LawID=42&Query=示例条例'):
    return f'''<input id="QueryAll" value="{query}"><input id="law-total" value="{count}"><input id="pageIndex" value="1">
<div>现行有效 <span>{count}</span> 部</div><ul class="searching-results-list"><li class="list-item"><div class="title"><a href="{detail_url}"><font>示例</font>条例</a></div><ul><li class="publish-date">2024-01-02公布</li><li class="implemented-date">2024-02-03施行</li></ul></li></ul>'''

class SearchAccuracyTests(unittest.TestCase):
    def test_official_gov_api_host_is_scoped_and_similar_hosts_stay_blocked(self):
        from research_runtime import OfficialClient, SourceBoundaryError
        from source_registry import official_source_for_url
        self.assertEqual(official_source_for_url('https://sousuoht.www.gov.cn/athena/forward/example').id,'gov-rules')
        self.assertIsNone(official_source_for_url('https://sousuoht.www.gov.cn.attacker.example/'))
        with self.assertRaises(SourceBoundaryError):
            OfficialClient('npc-law').validate_url('https://sousuoht.www.gov.cn/athena/forward/example')

    def test_npc_delegated_storage_is_https_exact_host_and_npc_only(self):
        from research_runtime import OfficialClient, SourceBoundaryError
        from source_registry import official_source_for_url
        resource='https://flkoss.obs-bj2.cucloud.cn/official-document.docx'
        self.assertEqual(OfficialClient('npc-law').validate_url(resource),resource)
        with self.assertRaises(SourceBoundaryError):
            OfficialClient('gov-rules').validate_url(resource)
        for url in ['http://flkoss.obs-bj2.cucloud.cn/file','https://flkoss.obs-bj2.cucloud.cn.attacker.example/file','https://other.obs-bj2.cucloud.cn/file']:
            self.assertIsNone(official_source_for_url(url))

    def test_delegated_storage_redirect_does_not_escape_registry(self):
        from unittest.mock import MagicMock
        from research_runtime import OfficialClient, SourceBoundaryError
        response=MagicMock()
        response.geturl.return_value='https://unregistered.example/document.docx'
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=response
        with self.assertRaises(SourceBoundaryError):
            OfficialClient('npc-law',opener=opener,requests_per_second=None).request('GET','https://flkoss.obs-bj2.cucloud.cn/document.docx')
        response.read.assert_not_called()

    def test_default_redirect_handler_rejects_before_creating_next_request(self):
        import urllib.request
        from research_runtime import OfficialClient, SourceBoundaryError, _SourceRedirectHandler
        client=OfficialClient('npc-law')
        handler=next(h for h in client.opener.handlers if isinstance(h,_SourceRedirectHandler))
        request=urllib.request.Request('https://flk.npc.gov.cn/start')
        for destination in ['https://unregistered.example/file','http://flk.npc.gov.cn/file','https://localhost/file']:
            with patch.object(urllib.request.HTTPRedirectHandler,'redirect_request') as create_next:
                with self.assertRaises(SourceBoundaryError):
                    handler.redirect_request(request,None,302,'Found',{},destination)
                create_next.assert_not_called()
        with patch.object(urllib.request.HTTPRedirectHandler,'redirect_request',return_value='allowed') as create_next:
            value=handler.redirect_request(request,None,302,'Found',{},'https://flkoss.obs-bj2.cucloud.cn/resource.docx')
            self.assertEqual(value,'allowed')
            create_next.assert_called_once()

    def test_moj_count_layout_mismatch_is_not_an_empty_success(self):
        for html in [page().split('<ul class="searching-results-list">')[0],page(count=0)]:
            with self.assertRaises(SourceAccessError):
                site_adapters.search_source('moj-regulations','示例条例',client=Client(html=html))

    def test_article_end_page_and_empty_page_have_no_cursor(self):
        for total in [0,1]:
            with patch.object(article_search,'search_laws',return_value={'code':200,'total':total,'rows':[]}):
                self.assertIsNone(article_search.search_articles('关键词',max_laws=1,client=Client({}))['next_offset'])

    def test_article_page_size_clamp_is_used_for_offset(self):
        with patch.object(article_search,'search_laws',return_value={'code':200,'total':0,'rows':[]}) as search:
            article_search.search_articles('关键词',max_laws=101,offset=100,client=Client({}))
        self.assertEqual(search.call_args.kwargs['size'],100)
        self.assertEqual(search.call_args.kwargs['page'],2)

    def test_exact_checks_title_and_status_without_changing_total_or_source(self):
        source={'code':200,'total':9,'rows':[{'title':'<em>示例法</em>','sxx':'3'},{'title':'示例法解释','sxx':3},{'title':'示例法','sxx':2}]}
        client=Client(source)
        result=download.search_laws('示例法',search_type=1,status_filter=[3],client=client)
        self.assertEqual(result['rows'],[source['rows'][0]])
        self.assertEqual(result['total'],9)
        self.assertEqual(len(source['rows']),3)
        self.assertEqual(result['query_window']['verified_rows'],1)
        self.assertEqual(len(client.calls),1)
    def test_missing_status_is_excluded(self):
        client=Client({'code':200,'total':1,'rows':[{'title':'示例法'}]})
        self.assertEqual(download.search_laws('示例法',status_filter=[3],client=client)['rows'],[])
    def test_no_exact_match_is_not_a_fuzzy_fallback(self):
        client=Client({'code':200,'total':1,'rows':[{'title':'示例法实施条例','sxx':3}]})
        self.assertEqual(download.search_laws('示例法',search_type=1,client=client)['rows'],[])
    def test_policy_existing_empty_url_fallback_remains(self):
        client=Client({'data':[{'title':'示例','piclinksurl':'','url':'https://sousuo.www.gov.cn/example.htm'}]})
        result=site_adapters.search_source('state-council-policy','示例',client=client)
        self.assertEqual(result[0]['detail_url'],'https://sousuo.www.gov.cn/example.htm')
    def test_moj_uses_current_form_and_extracts_fragmented_title_dates(self):
        client=Client(html=page())
        result=site_adapters.search_source('moj-regulations','示例条例',size=3,client=client)
        self.assertEqual(result[0]['title'],'示例条例')
        self.assertEqual(result[0]['promulgated_date'],'2024-01-02')
        self.assertEqual(result[0]['effective_date'],'2024-02-03')
        self.assertEqual(result[0]['status'],'现行有效')
        self.assertTrue(client.calls[0][1].endswith('/SearchTitleFront'))
        self.assertEqual(client.calls[0][2]['params']['QueryAll'],'示例条例ZVING1')
        detail_url=result[0]['detail_url']
        self.assertTrue(detail_url.isascii())
        self.assertEqual(parse_qs(urlsplit(detail_url).query)['Query'],['示例条例'])

    def test_moj_detail_extracts_legal_title_and_preamble_dates_without_inventing_status(self):
        url='https://xzfg.moj.gov.cn/front/law/detail?LawID=42&Query=%E7%A4%BA%E4%BE%8B'
        html='''<title>国家行政法规库</title><div class="content-text"><div class="text-bottom">
<div class="text-title">示例行政法规</div><div class="law-chapter">
<p><span>（2020年1月2日国务院第10次常务会议通过　2020年2月3日中华人民共和国国务院令第42号公布　自2020年4月5日起施行）</span></p>
<p>第一条　示例条文。</p></div></div></div>'''
        result=site_adapters.fetch_detail(url,client=Client(html=html))
        self.assertEqual(result['title'],'示例行政法规')
        self.assertEqual(result['publish_date'],'2020年2月3日')
        self.assertEqual(result['effective_date'],'2020年4月5日')
        self.assertEqual(result['issuing_body'],'国务院')
        self.assertEqual(result['document_number'],'国务院令第42号')
        self.assertEqual(result['status'],'未标注')
        self.assertIn('未标注效力状态',result['status_basis'])
    def test_moj_full_text_uses_verified_searchfront(self):
        client=Client(html=page(query='示例条例ZVING2'))
        site_adapters.search_source('moj-regulations','示例条例',search_range='content',client=client)
        self.assertTrue(client.calls[0][1].endswith('/SearchFront'))
    def test_moj_rejects_ignored_query_and_unsupported_status(self):
        with self.assertRaises(SourceAccessError):site_adapters.search_source('moj-regulations','示例条例',client=Client(html=page(query='别的ZVING1')))
        client=Client(html=page())
        with self.assertRaises(ValueError):site_adapters.search_source('moj-regulations','示例条例',filters={'status':'invalid'},client=client)
        self.assertEqual(client.calls,[])
    def test_gov_rules_only_title_field_uses_match(self):
        client=Client({'resultCode':{'code':200},'result':{'data':{'list':[]}}})
        with patch.object(site_adapters.GovRulesAuth,'discover',lambda self:self),patch.object(site_adapters.GovRulesAuth,'headers',return_value={}):
            site_adapters.search_source('gov-rules','管理办法',filters={'category':'部门规章'},client=client)
        searches=client.calls[0][2]['data']['searchFields']
        self.assertEqual(searches[1]['searchType'],'MATCH')
        self.assertEqual(searches[0]['searchType'],'TERM')
    def test_article_preamble_is_not_a_numbered_article(self):
        rows={'code':200,'total':1,'rows':[{'bbbs':'one','title':'示例法','sxx':3}]}
        with patch.object(article_search,'search_laws',return_value=rows),patch.object(article_search,'fetch_detail',return_value={'code':200,'data':{'title':'示例法','sxx':3}}),patch.object(article_search,'get_download_url',return_value='https://flk.npc.gov.cn/example.docx'),patch.object(article_search,'extract_docx_paragraphs',return_value=['示例关键词题注','第一条 普通正文。']):
            result=article_search.search_articles('关键词',client=Client({}))
        self.assertEqual(result['results'][0]['matched_articles'],0)
        self.assertEqual(result['results'][0]['matched_other_sections'],1)
    def test_article_status_rechecked_on_detail_before_download(self):
        rows={'code':200,'total':1,'rows':[{'bbbs':'one','title':'示例法','sxx':3}]}
        with patch.object(article_search,'search_laws',return_value=rows),patch.object(article_search,'fetch_detail',return_value={'code':200,'data':{'title':'示例法','sxx':1}}),patch.object(article_search,'get_download_url') as download_url:
            result=article_search.search_articles('关键词',status=3,client=Client({}))
        download_url.assert_not_called()
        self.assertEqual(result['results'][0]['error']['status'],'STATUS_MISMATCH')
    def test_article_offset_starts_at_raw_candidate_position(self):
        rows={'code':200,'total':3,'rows':[{'bbbs':'one','title':'甲'},{'bbbs':'two','title':'乙'}]}
        with patch.object(article_search,'search_laws',return_value=rows),patch.object(article_search,'fetch_detail',side_effect=SourceAccessError('not downloaded')):
            result=article_search.search_articles('关键词',max_laws=2,offset=1,client=Client({}))
        self.assertEqual([x['bbbs'] for x in result['results']],['two'])

if __name__=='__main__':unittest.main()
