import pylxd

from .provision import prepare_debian, provision_with_ansible, set_static_ip_on_debian
from .util import (
    ContainerStatus, get_ipv4_ip, get_config, get_default_gateway, find_free_ip,
    wait_for_ipv4_ip, get_container
)

def up():
    container = get_container()
    if container.status_code == ContainerStatus.Running:
        print("Container is already running!")
        return
    print("Starting container...")
    container.start(wait=True)
    if container.status_code != ContainerStatus.Running:
        print("Something went wrong trying to start the container.")
        return
    ip = get_ipv4_ip(container)
    if not ip:
        print("No IP yet, waiting 10 seconds...")
        ip = wait_for_ipv4_ip(container)
    if not ip:
        print("Still no IP! Forcing a static IP...")
        container.stop(wait=True)
        gateway = get_default_gateway()
        forced_ip = find_free_ip(gateway)
        set_static_ip_on_debian(container, forced_ip, gateway)
        container.start(wait=True)
        ip = wait_for_ipv4_ip(container)
    if ip:
        print("Container is up! IP: %s" % ip)
    else:
        print("STILL no IP! Container is up, but probably broken.")

def halt():
    container = get_container()
    if container.status_code == ContainerStatus.Stopped:
        print("The container is already stopped.")
        return
    print("Stopping...")
    try:
        container.stop(timeout=30, force=False, wait=True)
    except pylxd.exceptions.LXDAPIException:
        print("Can't stop the container. Forcing...")
        container.stop(force=True, wait=True)

def provision():
    config = get_config()
    container = get_container()
    if container.status_code != ContainerStatus.Running:
        print("The container is not running.")
        return

    print("Doing bare bone setup on the machine...")
    prepare_debian(container)

    print("Provisioning container...")
    for provisioning_item in config['provisioning']:
        print("Provisioning with {}".format(provisioning_item['type']))
        provision_with_ansible(container, provisioning_item)

def destroy():
    container = get_container(create=False)
    if container is None:
        print("Container doesn't exist, nothing to destroy.")
        return

    halt()
    container = get_container()
    print("Destroying...")
    container.delete(wait=True)
    print("Destroyed!")

