#!/bin/bash

# 1. Get OS version

if [ -f /etc/redhat-release ] ; then
  DIST=`cat /etc/redhat-release | awk '{print $1}'`
  CODENAME=`cat /etc/redhat-release | sed s/.*\(// | sed s/\)//`
  REV=`cat /etc/redhat-release | awk '{print $3,$4}' | grep -o "[0-9.]*"`
elif [ -f /etc/lsb-release ] ; then
  DIST=`cat /etc/lsb-release | grep DISTRIB_ID | tr "\n" ' '| sed s/.*=//`
  REV=`cat /etc/lsb-release | grep DISTRIB_RELEASE | tr "\n" ' '| sed s/.*=//`
  CODENAME=`cat /etc/lsb-release | grep DISTRIB_CODENAME | tr "\n" ' '| sed s/.*=//`
elif [ -f /etc/os-release ] ; then
  DIST=`grep -e "^NAME=" /etc/os-release | awk -F\" '{print $2}'`
  REV=`grep -e "^VERSION_ID=" /etc/os-release | awk -F\" '{print $2}'`
  CODENAME=`grep -e "^PRETTY_NAME=" /etc/os-release | awk -F\" '{print $2}'`
fi

if [[ ! $REV =~ ^8.* ]] && [[ ! $REV =~ ^7.* ]];then
  echo "This script can ONLY be executed on CentOS/Rocky 7/8"
  exit 1
fi

# 2. Install packages

if [[ $REV =~ ^7.* ]];then
  yum install -y epel-release sshpass
  rpm -qa |grep python2-pip || yum install -y python2-pip

  pip install pip==20.3.4
  pip install requests
  pip install --ignore-installed PyYAML
  pip install ansible==2.7.18
elif [[ $REV =~ ^8.* ]];then
  pip3 -V || yum install -y python3-pip
  pip3 install --upgrade pip
  pip3 install requests
  pip3 install --upgrade PyYAML
  ls /usr/bin/python || ln -s /usr/bin/python3 /usr/bin/python

  ansible-playbook -v || yum install -y epel-release && yum install -y ansible
  pip3 install --upgrade ansible
fi

# 3. Configure instances

ansible-playbook -i inventory/ -e orchestrator=none playbooks/configure_instances.yml && \

# 4. Install contrail

ansible-playbook -i inventory/ -e orchestrator=none playbooks/install_contrail.yml && \

# 5. DONE

ui_ip=$(python -c "
import yaml
configs=yaml.safe_load(open('config/instances.yaml'))
ui_ip=None
for server in configs['instances']:
    if 'webui' in configs['instances'][server]['roles'].keys():
        ui_ip=configs['instances'][server]['ip']
        break
print(ui_ip)
") && \

echo "Tungsten has been installed successfully." && \
echo "Please access the web UI using admin/contrail123" && \
echo "- https://${ui_ip}:8143" && \
echo "- http://${ui_ip}:8180"
