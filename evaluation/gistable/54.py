from fabric.api import env, local, run
 
def vagrant():
    # change from the default user to 'vagrant'
    env.user = 'vagrant'
    # connect to the port-forwarded ssh
    env.hosts = ['127.0.0.1:2222']
 
    # use vagrant ssh key
    result = local('vagrant ssh_config | grep IdentityFile', capture=True)
    env.key_filename = result.split()[1]
 
def uname():
    run('uname -a')