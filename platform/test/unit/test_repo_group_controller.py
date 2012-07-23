# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import base
import mock_plugins

from pulp.server.db.model.repository import Repo
from pulp.server.db.model.repo_group import RepoGroup, RepoGroupDistributor, RepoGroupPublishResult
from pulp.server.managers import factory as manager_factory

class RepoGroupCollectionTests(base.PulpWebserviceTests):

    def setUp(self):
        super(RepoGroupCollectionTests, self).setUp()

        self.manager = manager_factory.repo_group_manager()

    def clean(self):
        super(RepoGroupCollectionTests, self).clean()

        Repo.get_collection().remove()
        RepoGroup.get_collection().remove()

    def test_get(self):
        # Setup
        self.manager.create_repo_group('group-1')
        self.manager.create_repo_group('group-2')

        # Test
        status, body = self.get('/v2/repo_groups/')

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(2, len(body))

        ids = [g['id'] for g in body]
        self.assertTrue('group-1' in ids)
        self.assertTrue('group-2' in ids)

    def test_get_no_groups(self):
        # Test
        status, body = self.get('/v2/repo_groups/')

        # Verify
        self.assertEqual(200, status)
        self.assertTrue(isinstance(body, list))
        self.assertEqual(0, len(body))

    def test_post(self):
        # Setup
        data = {
            'id' : 'post-group',
            'display_name' : 'Post Group',
            'description' : 'Post Description',
        }

        # Test
        status, body = self.post('/v2/repo_groups/', data)

        # Verify
        self.assertEqual(201, status)

        found = RepoGroup.get_collection().find_one({'id' : data['id']})
        self.assertTrue(found is not None)
        for k, v in data.items():
            self.assertEqual(found[k], v)

    def test_post_missing_value(self):
        # Test
        status, body = self.post('/v2/repo_groups/', {})

        # Verify
        self.assertEqual(400, status)

    def test_post_extra_keys(self):
        # Test
        status, body = self.post('/v2/repo_groups/', {'extra' : 'e'})

        # Verify
        self.assertEqual(400, status)

    def test_post_with_repos(self):
        # Setup
        manager_factory.repo_manager().create_repo('add-me')

        data = {
            'id' : 'with-repos',
            'repo_ids' : ['add-me']
        }

        # Test
        status, body = self.post('/v2/repo_groups/', data)

        # Verify
        self.assertEqual(201, status)

        found = RepoGroup.get_collection().find_one({'id' : data['id']})
        self.assertEqual(found['repo_ids'], data['repo_ids'])

class RepoGroupResourceTests(base.PulpWebserviceTests):

    def setUp(self):
        super(RepoGroupResourceTests, self).setUp()

        self.manager = manager_factory.repo_group_manager()

    def clean(self):
        super(RepoGroupResourceTests, self).clean()

        RepoGroup.get_collection().remove()

    def test_get(self):
        # Setup
        group_id = 'created'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.get('/v2/repo_groups/%s/' % group_id)

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(body['id'], group_id)

    def test_get_missing_group(self):
        # Test
        status, body = self.get('/v2/repo_groups/missing/')

        # Verify
        self.assertEqual(404, status)

    def test_delete(self):
        # Setup
        group_id = 'doomed'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.delete('/v2/repo_groups/%s/' % group_id)

        # Verify
        self.assertEqual(200, status)

        found = RepoGroup.get_collection().find_one({'id' : group_id})
        self.assertTrue(found is None)
        self.assertEqual(body, None)

    def test_delete_missing_group(self):
        # Test
        status, body = self.delete('/v2/repo_groups/missing/')

        # Verify
        self.assertEqual(404, status)

    def test_update(self):
        # Setup
        group_id = 'update-me'
        self.manager.create_repo_group(group_id, display_name='Original')

        # Test
        changed = {'display_name' : 'Updated'}
        status, body = self.put('/v2/repo_groups/%s/' % group_id, changed)

        # Verify
        self.assertEqual(200, status)

        found = RepoGroup.get_collection().find_one({'id' : group_id})
        self.assertEqual(changed['display_name'], found['display_name'])

class RepoGroupDistributorsTests(base.PulpWebserviceTests):

    def setUp(self):
        super(RepoGroupDistributorsTests, self).setUp()

        mock_plugins.install()

        self.manager = manager_factory.repo_group_manager()
        self.distributor_manager = manager_factory.repo_group_distributor_manager()

    def clean(self):
        super(RepoGroupDistributorsTests, self).clean()

        RepoGroup.get_collection().remove()
        RepoGroupDistributor.get_collection().remove()

    def test_get(self):
        # Setup
        group_id = 'dist-group'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id='dist-1')
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id='dist-2')

        # Test
        status, body = self.get('/v2/repo_groups/%s/distributors/' % group_id)

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(2, len(body))
        ids = [d['id'] for d in body]
        self.assertTrue('dist-1' in ids)
        self.assertTrue('dist-2' in ids)

    def test_get_no_distributors(self):
        # Setup
        group_id = 'dist-group'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.get('/v2/repo_groups/%s/distributors/' % group_id)

        # Verify
        self.assertEqual(200, status)
        self.assertTrue(isinstance(body, list))
        self.assertEqual(0, len(body))

    def test_post(self):
        # Setup
        group_id = 'group-1'
        self.manager.create_repo_group(group_id)

        # Test
        data = {
            'distributor_type_id' : 'mock-group-distributor',
            'distributor_config' : {'a' : 'A'},
            'distributor_id' : 'dist-1',
        }
        status, body = self.post('/v2/repo_groups/%s/distributors/' % group_id, data)

        # Verify
        self.assertEqual(201, status)
        self.assertEqual(body['id'], data['distributor_id'])

        found = RepoGroupDistributor.get_collection().find_one({'id' : data['distributor_id']})
        self.assertTrue(found is not None)

class RepoGroupDistributorTests(base.PulpWebserviceTests):

    def setUp(self):
        super(RepoGroupDistributorTests, self).setUp()

        mock_plugins.install()

        self.manager = manager_factory.repo_group_manager()
        self.distributor_manager = manager_factory.repo_group_distributor_manager()

    def clean(self):
        super(RepoGroupDistributorTests, self).clean()

        RepoGroup.get_collection().remove()
        RepoGroupDistributor.get_collection().remove()

    def test_get(self):
        # Setup
        group_id = 'dist-group'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id='dist-1')
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id='dist-2')

        # Test
        status, body = self.get('/v2/repo_groups/%s/distributors/%s/' % (group_id, 'dist-1'))

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(body['id'], 'dist-1')

    def test_get_missing_group(self):
        # Test
        status, body = self.get('/v2/repo_groups/foo/distributors/irrelevant/')

        # Verify
        self.assertEqual(404, status)

    def test_get_missing_distributor(self):
        # Setup
        group_id = 'missing-dist'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.get('/v2/repo_groups/%s/distributors/missing/' % group_id)

        # Verify
        self.assertEqual(404, status)

    def test_delete(self):
        # Setup
        group_id = 'group'
        distributor_id = 'created'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id=distributor_id)

        # Test
        status, body = self.delete('/v2/repo_groups/%s/distributors/%s/' % (group_id, distributor_id))

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(body, None)

        found = RepoGroupDistributor.get_collection().find_one({'id' : distributor_id})
        self.assertEqual(found, None)

    def test_delete_missing_group(self):
        # Test
        status, body = self.delete('/v2/repo_groups/missing/distributors/irrelevant/')

        # Verify
        self.assertEqual(404, status)

    def test_delete_missing_distributor(self):
        # Setup
        group_id = 'doomed'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.delete('/v2/repo_groups/%s/distributors/missing/' % group_id)

        # Verify
        self.assertEqual(404, status)

    def test_put(self):
        # Setup
        group_id = 'group-1'
        distributor_id = 'dist-1'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {'a' : 'A'}, distributor_id=distributor_id)

        # Test
        updated_config = {'b' : 'B'}
        status, body = self.put('/v2/repo_groups/%s/distributors/%s/' % (group_id, distributor_id), {'distributor_config' : updated_config})

        # Verify
        self.assertEqual(200, status)
        self.assertEqual(body['id'], distributor_id)

        found = RepoGroupDistributor.get_collection().find_one({'id' : distributor_id})
        self.assertEqual(found['config'], {'a' : 'A', 'b' : 'B'})

    def test_put_extra_data(self):
        # Setup
        group_id = 'group-1'
        distributor_id = 'dist-1'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {'a' : 'A'}, distributor_id=distributor_id)

        # Test
        status, body = self.put('/v2/repo_groups/%s/distributors/%s/' % (group_id, distributor_id), {'foo' : 'bar'})

        # Verify
        self.assertEqual(400, status)

    def test_put_missing_group(self):
        # Test
        status, body = self.put('/v2/repo_groups/missing/distributors/irrelevant/', {'distributor_config' : {}})

        # Verify
        self.assertEqual(404, status)

    def test_put_missing_distributor(self):
        # Setup
        group_id = 'empty'
        self.manager.create_repo_group(group_id)

        # Test
        status, body = self.put('/v2/repo_groups/%s/distributors/missing/' % group_id, {'distributor_config' : {}})

        # Verify
        self.assertEqual(404, status)

class PublishActionTests(base.PulpWebserviceTests):

    def setUp(self):
        super(PublishActionTests, self).setUp()

        mock_plugins.install()

        self.manager = manager_factory.repo_group_manager()
        self.distributor_manager = manager_factory.repo_group_distributor_manager()

    def clean(self):
        super(PublishActionTests, self).clean()

        RepoGroup.get_collection().remove()
        RepoGroupDistributor.get_collection().remove()

    def test_post(self):
        # Setup
        group_id = 'group-1'
        distributor_id = 'dist-1'
        self.manager.create_repo_group(group_id)
        self.distributor_manager.add_distributor(group_id, 'mock-group-distributor', {}, distributor_id=distributor_id)

        # Test
        data = {'id' : distributor_id}
        status, body = self.post('/v2/repo_groups/%s/actions/publish/' % group_id, data)

        # Verify
#        self.assertEqual(202, status)