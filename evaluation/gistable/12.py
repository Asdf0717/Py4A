import plistlib
import CoreFoundation
from Foundation import NSDate, NSMutableArray, NSMutableDictionary

# read the current ManagedPlugInPolicies
policy = CoreFoundation.CFPreferencesCopyAppValue("ManagedPlugInPolicies", "com.apple.Safari")

if policy:
    # policy is an immutable dict, so we have to make a mutable copy
    my_policy = NSMutableDictionary.alloc().initWithDictionary_copyItems_(policy, True)
else:
    # create an empty dict
    my_policy = {}

if 'com.oracle.java.JavaAppletPlugin' in my_policy:
    # make a mutable copy of the dict
    current_dict = my_policy['com.oracle.java.JavaAppletPlugin']
    my_policy['com.oracle.java.JavaAppletPlugin'] = NSMutableDictionary.alloc().initWithDictionary_copyItems_(current_dict, True)
else:
    # create an empty dict
    my_policy['com.oracle.java.JavaAppletPlugin'] = {}

if 'PlugInHostnamePolicies' in my_policy['com.oracle.java.JavaAppletPlugin']:
    # make a mutable copy of the array
    current_array = my_policy['com.oracle.java.JavaAppletPlugin']['PlugInHostnamePolicies']
    my_policy['com.oracle.java.JavaAppletPlugin']['PlugInHostnamePolicies'] = NSMutableArray.alloc().initWithArray_(current_array)
else:
    # create an empty array
    my_policy['com.oracle.java.JavaAppletPlugin']['PlugInHostnamePolicies'] = []

found_foocorp_vpn = False
# iterate through dicts in com.oracle.java.JavaAppletPlugin:PlugInHostnamePolicies
for dict_item in my_policy['com.oracle.java.JavaAppletPlugin']['PlugInHostnamePolicies']:
    if dict_item.get('PlugInHostname') == 'vpn.foocorp.com':
        found_foocorp_vpn = True

if not found_foocorp_vpn:
    foocorp_vpn = { 'PlugInPageURL': 'https://vpn.foocorp.com/index.cgi',
                     'PlugInHostname': 'vpn.foocorp.com',
                     'PlugInRunUnsandboxed': True,
                     'PlugInPolicy': 'PlugInPolicyAllowNoSecurityRestrictions',
                     'PlugInLastVisitedDate': NSDate.date() }
    # add our new policy to the array
    my_policy['com.oracle.java.JavaAppletPlugin']['PlugInHostnamePolicies'].append(foocorp_vpn)

# save the changed preference
CoreFoundation.CFPreferencesSetAppValue("ManagedPlugInPolicies", my_policy,  "com.apple.Safari")
