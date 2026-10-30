import copy
import hashlib
import unittest
from scrapers.sudameris_scoped_reviews import apply_scoped_reviews, fingerprint


class ScopedReviewTests(unittest.TestCase):
    def fixture(self):
        row={'URL':'official','Comercio/Promoción':'Merchant','Variante':'base','Vigencia':'old'}
        fields=list(row)
        new={**row,'Vigencia':'new'}
        review={'documents':{'https://www.sudameris.com.py/x.pdf':hashlib.sha256(b'pdf').hexdigest()},'fingerprint_fields':fields,'mutations':[{'selector':row,'accepted_sha256':[fingerprint(row,fields),fingerprint(new,fields)],'patch':{'Vigencia':'new'}}],'additions':[]}
        return row,review

    def test_hash_change_fails_without_mutating_input(self):
        row,review=self.fixture();before=copy.deepcopy(row)
        with self.assertRaisesRegex(ValueError,'document changed'):
            apply_scoped_reviews([row],review,lambda _:b'new pdf')
        self.assertEqual(row,before)

    def test_changed_campaign_cannot_silently_reuse_review(self):
        row,review=self.fixture();row['Vigencia']='other campaign'
        with self.assertRaisesRegex(ValueError,'row changed'):
            apply_scoped_reviews([row],review,lambda _:b'pdf')

    def test_missing_identity_is_not_hidden(self):
        _,review=self.fixture()
        with self.assertRaisesRegex(ValueError,'Missing reviewed'):
            apply_scoped_reviews([],review,lambda _:b'pdf')

    def test_repeat_is_idempotent_and_preserves_history(self):
        row,review=self.fixture();history={'URL':'old','Comercio/Promoción':'Expired','Vigencia':'2025'}
        once=apply_scoped_reviews([row,history],review,lambda _:b'pdf')
        self.assertEqual(once,apply_scoped_reviews(once,review,lambda _:b'pdf'))
        self.assertEqual(once[1],history)

    def test_partial_mode_does_not_reuse_changed_document(self):
        row,review=self.fixture();review['mutations'][0]['documents']=list(review['documents'])
        failures=[]
        result=apply_scoped_reviews([row],review,lambda _:b'changed',failures=failures)
        self.assertEqual(result[0]['Vigencia'],'old')
        self.assertEqual(result[0]['Estado verificacion'],'unconfirmed')
        self.assertEqual(len(failures),1)

    def test_partial_mode_validates_unaffected_reviews(self):
        row,review=self.fixture();review['mutations'][0]['documents']=list(review['documents'])
        review['documents']['other']=hashlib.sha256(b'original').hexdigest()
        failures=[]
        result=apply_scoped_reviews([row],review,lambda u:b'changed' if u=='other' else b'pdf',failures=failures)
        self.assertEqual(result[0]['Vigencia'],'new')
        self.assertEqual(len(failures),1)

    def test_missing_document_retains_only_existing_addition_unconfirmed(self):
        import requests
        row,review=self.fixture();review['mutations']=[]
        review['additions']=[{'row':{**row,'Vigencia':'new'},'documents':list(review['documents'])}]
        def fail(_):raise requests.HTTPError('404')
        failures=[]
        self.assertEqual(apply_scoped_reviews([],review,fail,failures=failures),[])
        result=apply_scoped_reviews([row],review,fail,failures=[])
        self.assertEqual(result[0]['Vigencia'],'old')
        self.assertEqual(result[0]['Estado verificacion'],'unconfirmed')

    def test_replacement_requires_exact_prior_row_fingerprint(self):
        row,review=self.fixture();review['mutations']=[]
        review['additions']=[{'row':{**row,'Vigencia':'reviewed'},'accepted_sha256':[fingerprint(row,review['fingerprint_fields'])]}]
        self.assertEqual(apply_scoped_reviews([row],review,lambda _:b'pdf')[0]['Vigencia'],'reviewed')
        with self.assertRaisesRegex(ValueError,'merchant changed'):
            apply_scoped_reviews([{**row,'Vigencia':'unknown'}],review,lambda _:b'pdf')
