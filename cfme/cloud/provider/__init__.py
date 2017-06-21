""" A model of a Cloud Provider in CFME


:var page: A :py:class:`cfme.web_ui.Region` object describing common elements on the
           Providers pages.
:var discover_form: A :py:class:`cfme.web_ui.Form` object describing the discover form.
:var properties_form: A :py:class:`cfme.web_ui.Form` object describing the main add form.
:var default_form: A :py:class:`cfme.web_ui.Form` object describing the default credentials form.
:var amqp_form: A :py:class:`cfme.web_ui.Form` object describing the AMQP credentials form.
"""

from functools import partial

from navmazing import NavigateToSibling, NavigateToAttribute
from widgetastic_manageiq import TimelinesView

from cfme.base.login import BaseLoggedInPage
from cfme.common.provider_views import (CloudProviderAddView,
                                        CloudProviderEditView,
                                        CloudProviderDetailsView,
                                        CloudProvidersView,
                                        CloudProvidersDiscoverView,
                                        ProvidersManagePoliciesView,
                                        ProvidersEditTagsView)
import cfme.fixtures.pytest_selenium as sel
from cfme.common.provider import CloudInfraProvider
from cfme.web_ui import form_buttons
from cfme.web_ui import toolbar as tb
from cfme.web_ui import Region, fill, paginator, InfoBlock, match_location
from utils.appliance import Navigatable
from utils.appliance.implementations.ui import navigator, navigate_to, CFMENavigateStep
from utils.log import logger
from utils.wait import wait_for
from utils.pretty import Pretty


details_page = Region(infoblock_type='detail')

match_page = partial(match_location, controller='ems_cloud', title='Cloud Providers')


class CloudProviderTimelinesView(TimelinesView, BaseLoggedInPage):
    @property
    def is_displayed(self):
        return self.logged_in_as_current_user and \
            self.navigation.currently_selected == ['Compute', 'Clouds', 'Providers'] and \
            super(TimelinesView, self).is_displayed


class CloudProvider(Pretty, CloudInfraProvider):
    """
    Abstract model of a cloud provider in cfme. See EC2Provider or OpenStackProvider.

    Args:
        name: Name of the provider.
        details: a details record (see EC2Details, OpenStackDetails inner class).
        credentials (:py:class:`Credential`): see Credential class.
        key: The CFME key of the provider in the yaml.

    Usage:

        myprov = EC2Provider(name='foo',
                             region='us-west-1',
                             credentials=Credential(principal='admin', secret='foobar'))
        myprov.create()

    """
    provider_types = {}
    category = "cloud"
    pretty_attrs = ['name', 'credentials', 'zone', 'key']
    STATS_TO_MATCH = ['num_template', 'num_vm']
    string_name = "Cloud"
    page_name = "clouds"
    templates_destination_name = "Images"
    vm_name = "Instances"
    template_name = "Images"
    db_types = ["CloudManager"]

    def __init__(self, name=None, endpoints=None, zone=None, key=None, appliance=None):
        Navigatable.__init__(self, appliance=appliance)
        self.name = name
        self.zone = zone
        self.key = key
        self.endpoints = self._prepare_endpoints(endpoints)

    def as_fill_value(self):
        return self.name

    @property
    def view_value_mapping(self):
        return {'name': self.name}


@navigator.register(CloudProvider, 'All')
class All(CFMENavigateStep):
    VIEW = CloudProvidersView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Clouds', 'Providers')

    def resetter(self):
        tb = self.view.toolbar
        paginator = self.view.paginator
        if 'Grid View' not in tb.view_selector.selected:
            tb.view_selector.select('Grid View')
        if paginator.exists:
            paginator.check_all()
            paginator.uncheck_all()


@navigator.register(CloudProvider, 'Add')
class New(CFMENavigateStep):
    VIEW = CloudProviderAddView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select('Add a New Cloud Provider')


@navigator.register(CloudProvider, 'Discover')
class Discover(CFMENavigateStep):
    VIEW = CloudProvidersDiscoverView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select('Discover Cloud Providers')


@navigator.register(CloudProvider, 'Details')
class Details(CFMENavigateStep):
    VIEW = CloudProviderDetailsView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.items.get_item(by_name=self.obj.name).click()


@navigator.register(CloudProvider, 'Edit')
class Edit(CFMENavigateStep):
    VIEW = CloudProviderEditView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.items.get_item(by_name=self.obj.name).check()
        self.prerequisite_view.toolbar.configuration.item_select('Edit Selected Cloud Provider')


@navigator.register(CloudProvider, 'EditFromDetails')
class EditFromDetails(CFMENavigateStep):
    VIEW = CloudProviderEditView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select('Edit this Cloud Provider')


@navigator.register(CloudProvider, 'ManagePolicies')
class ManagePolicies(CFMENavigateStep):
    VIEW = ProvidersManagePoliciesView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.items.get_item(by_name=self.obj.name).check()
        self.prerequisite_view.toolbar.policy.item_select('Manage Policies')


@navigator.register(CloudProvider, 'ManagePoliciesFromDetails')
class ManagePoliciesFromDetails(CFMENavigateStep):
    VIEW = ProvidersManagePoliciesView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.policy.item_select('Manage Policies')


@navigator.register(CloudProvider, 'EditTags')
class EditTags(CFMENavigateStep):
    VIEW = ProvidersEditTagsView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.items.get_item(by_name=self.obj.name).check()
        self.prerequisite_view.toolbar.policy.item_select('Edit Tags')


@navigator.register(CloudProvider, 'EditTagsFromDetails')
class EditTagsFromDetails(CFMENavigateStep):
    VIEW = ProvidersEditTagsView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.policy.item_select('Edit Tags')


@navigator.register(CloudProvider, 'Timelines')
class Timelines(CFMENavigateStep):
    VIEW = CloudProviderTimelinesView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        mon = self.prerequisite_view.toolbar.monitoring
        mon.item_select('Timelines')


@navigator.register(CloudProvider, 'Instances')
class Instances(CFMENavigateStep):
    prerequisite = NavigateToSibling('Details')

    def am_i_here(self):
        return match_page(summary='{} (All Instances)'.format(self.obj.name))

    def step(self, *args, **kwargs):
        sel.click(InfoBlock.element('Relationships', 'Instances'))


@navigator.register(CloudProvider, 'Images')
class Images(CFMENavigateStep):
    prerequisite = NavigateToSibling('Details')

    def am_i_here(self):
        return match_page(summary='{} (All Images)'.format(self.obj.name))

    def step(self, *args, **kwargs):
        sel.click(InfoBlock.element('Relationships', 'Images'))


def get_all_providers(do_not_navigate=False):
    """Returns list of all providers"""
    if not do_not_navigate:
        navigate_to(CloudProvider, 'All')
    providers = set([])
    link_marker = "ems_cloud"
    for page in paginator.pages():
        for title in sel.elements("//div[@id='quadicon']/../../../tr/td/a[contains(@href,"
                "'{}/show')]".format(link_marker)):
            providers.add(sel.get_attribute(title, "title"))
    return providers


def discover(credential, cancel=False, d_type="Amazon"):
    """
    Discover cloud providers. Note: only starts discovery, doesn't
    wait for it to finish.

    Args:
      credential (cfme.base.credential.Credential):  Amazon discovery credentials.
      cancel (boolean):  Whether to cancel out of the discover UI.
      d_type: provider name which will be discovered
    """
    view = navigate_to(CloudProvider, 'Discover')
    view.fill({'discover_type': d_type,
               'username': credential.principal,
               'password': credential.secret,
               'password_verify': credential.verify_secret})
    if cancel:
        view.cancel.click()
    else:
        view.start.click()


def wait_for_a_provider():
    view = navigate_to(CloudProvider, 'All')
    logger.info('Waiting for a provider to appear...')
    wait_for(lambda: int(view.paginator.items_amount), fail_condition=0,
             message="Wait for any provider to appear", num_sec=1000,
             fail_func=view.browser.selenium.refresh)
