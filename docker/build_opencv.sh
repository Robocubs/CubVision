# Start by building the docker image
docker build --tag 'opencv_build' .

# Run the container and grab the id
CONTAINER_ID=$(docker run --detach 'opencv_build')

# Clean any previous dirs
rm -r ./cv2
rm -r ./lib

# Copy the python package directory
docker cp "$CONTAINER_ID":/usr/local/lib/python3.10/dist-packages/cv2/ .

# Copy the built shared objects
"""
WARNING: This copies EVERYTHING, including the shared objects. Since we're in a docker container, 
there really shouldn't be anything else installed here.
"""
docker cp "$CONTAINER_ID":/usr/local/lib/ .

# TODO: Get these automatically implemented, do not copy dirs in lib though
#scp -r ./lib/ root@10.0.100.139:/usr/local/lib 
#scp -r ./cv2 root@10.0.100.139:/usr/local/lib/python3.10/dist-packages/