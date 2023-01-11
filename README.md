# checkbox-provider-ce-oem
This is a checkbox provider for both IoT and PC devices. And it will be build as SNAP named *checkbox-ce-oem*. 
You can define specific plugs to connect to it and start using the test jobs and plans included in checkbox-provider-ce-oem.

# Getting started
checkbox-ce-oem will define a slot *provider-ce-oem* to allow checkbox to connect to access the test jobs and plans.

## In checkbox
You have to modify two parts and rebuild your SNAP of checkbox.
### snapcraft.yaml
Add a plug into plugs section in *snapcraft.yaml* of your checkbox.
```
example:

plugs:
    provider-ce-oem:
    interface: content
    target: $SNAP/providers/checkbox-provider-ce-oem
    default-provider: checkbox-ce-oem
```
### wrapper_local
Add export PATH for checkbox-ce-oem in *wrapper_local* of your checkbox.
```
example:
export PATH="$PATH:$SNAP/usr/bin:$SNAP/usr/sbin:$SNAP/sbin:/snap/bin:$SNAP/bin:/snap/checkbox-ce-oem/current/usr/bin/:/snap/checkbox-ce-oem/current/usr/sbin"
```
### After rebuild SNAP for checkbox
Install the SNAP of checkbox and checkbox-ce-oem. Connect slot and plug of *provider-ce-oem*.

`$ sudo snap connect checkbox:provider-ce-oem checkbox-ce-oem`

### Start to using test jobs and plans in checkbox-provider-ce-oem
Now, you are able to include the job, plan or utility from checkbox-provider-ce-oem.
```
example for running a job:
$ sudo checkbox.checkbox-cli run com.canonical.qa.ceoem::location/gps_coordinate

example for using utility:
$ sudo checkbox.shell
$ checkbox.shell> lsmtd
```
