import unittest

from promo_backend.quality import favorite_aliases


class FavoriteCampaignTests(unittest.TestCase):
    def setUp(self):
        self.old = {'id': 'campaign', 'bank': 'Familiar', 'merchant_name': 'Comercio', 'category': 'Gastronomía'}
        self.current = [{**self.old, 'id': 'platinum', 'campaign_id': 'campaign'},
                        {**self.old, 'id': 'gold', 'campaign_id': 'campaign'}]

    def test_split_keeps_the_existing_campaign_key(self):
        self.assertEqual(favorite_aliases([self.old], self.current), {})

    def test_alias_chain_can_target_a_campaign_without_a_row_of_that_id(self):
        self.assertEqual(favorite_aliases([], self.current, {'older': 'old', 'old': 'campaign'}),
                         {'older': 'campaign', 'old': 'campaign'})

    def test_renewal_maps_all_old_variants_to_new_campaign(self):
        renewed = [{**p, 'id': p['id'] + '-new', 'campaign_id': 'new-campaign'} for p in self.current]
        self.assertEqual(favorite_aliases(self.current, renewed),
                         {'campaign': 'new-campaign', 'platinum': 'new-campaign', 'gold': 'new-campaign'})

    def test_two_distinct_campaigns_still_remain_ambiguous(self):
        alternatives = [self.current[0], {**self.current[1], 'campaign_id': 'other-campaign'}]
        self.assertEqual(favorite_aliases([{**self.old, 'id': 'old'}], alternatives), {})

    def test_other_banks_keep_legacy_one_to_one_aliasing(self):
        old = {**self.old, 'bank': 'Other', 'id': 'old'}
        self.assertEqual(favorite_aliases([old], [{**old, 'id': 'new'}]), {'old': 'new'})


if __name__ == '__main__':
    unittest.main()
