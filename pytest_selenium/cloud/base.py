# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from abc import ABCMeta, abstractmethod, abstractproperty


class CloudProvider:
    __metaclass__ = ABCMeta

    def split_class_and_test_names(self, nodeid):
        """Returns the class and method name from the current test"""
        names = nodeid.split('::')
        names[0] = names[0].replace('/', '.')
        names = [x.replace('.py', '') for x in names if x != '()']
        classnames = names[:-1]
        classname = '.'.join(classnames)
        name = names[-1]
        return (classname, name)

    @abstractproperty
    def name(self):
        """Abstract property for the cloud provider name"""
        return

    @abstractmethod
    def start_driver(item, capabilities):
        """Abstract method for starting and returning the WebDriver instance"""
        return

    @abstractmethod
    def url(config, session):
        """Abstract method for returning the session URL"""
        return

    def additional_html(session):
        """Implement this method to return additional HTML for reports"""
        return []

    def update_status(config, session, passed):
        """Implement this method to submit results to the cloud provider"""
        pass
