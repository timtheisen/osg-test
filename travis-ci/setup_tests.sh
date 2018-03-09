#!/bin/sh -xe

# This script starts docker and systemd (if el7)

# Run tests in Container
# We use `--privileged` for cgroup compatability, which seems to be enabled by default in HTCondor 8.6.x
if [ "${OS_VERSION}" = "6" ]; then

sudo docker run --privileged --rm=true -v /sys/fs/cgroup:/sys/fs/cgroup -v `pwd`:/osg-test:rw centos:centos${OS_VERSION} /bin/bash -c "bash -xe /osg-test/travis-ci/test_inside_docker.sh ${OS_VERSION} ${PACKAGES}"

elif [ "${OS_VERSION}" = "7" ]; then

docker run --privileged -d -ti -e "container=docker"  -v /sys/fs/cgroup:/sys/fs/cgroup -v `pwd`:/osg-test:rw  centos:centos${OS_VERSION}   /usr/sbin/init
DOCKER_CONTAINER_ID=$(docker ps | grep centos | awk '{print $1}')
docker logs $DOCKER_CONTAINER_ID
docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -xec "bash -xe /osg-test/travis-ci/test_inside_docker.sh ${OS_VERSION} ${PACKAGES};
  echo -ne \"------\nEND OSG-TEST TESTS\n\";"
docker ps -a
docker stop $DOCKER_CONTAINER_ID
docker rm -v $DOCKER_CONTAINER_ID

fi

