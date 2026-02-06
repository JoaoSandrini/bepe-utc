# Performance Impact of Isolation in Edge-Cloud Platforms for Intelligent Transportation Systems - Dataset and Plots

This project is a datset resulted of the BEPE project number 2025/14162-0, financed By FAPESP.

## 1. Context

This project have the objetive of testing different isolation tachniques when deploying an ITS application, specificlly an Advanced Driving Assistance System, in a StarlingX Edge Cloud Platform.

It was developed in the Heudiasyc Laboratory at Université de technologie de Compiégne, France. The ADAS application developed in the laboratory was deployed in a StarlingX server as CaaS. Another computer was use to send ROS2 messages to the server, which had to process the data and generate perceptions using the YOLO framework.

## 2. Directories

**/scripts -** Folder containing the scripts used to automate the tests.

### 2.1 Data Directiories

**/base -** Tests using kubernetes default runtime (runc).

**/kata -** Tests using Kata Containers runtime.

**/mixed -** Tests using both runtimes.

### 2.2 Subdirectories

**/<base, kata>/off -** The only workload running during tests was the ADAS application.

**/<base, kata>/on -** A CPU stressor pod was also deployed to generate load and stress the CPU, raising usage to 100% when combined with the ADAS application.

**/mixed/kata -** ADAS application deployed using Kata Containers, CPU stressor using runc.

**/mixed/default -** ADAS applicatio deployed using runc, CPU stressor using Kata Containers.

### 2.3 Data directories

**-> Index at the end of files shows iteration number. 10 iterations per test.**

**/\*/\*/delays -** Output of "ros2 topic delay" of input (/points) and output (/perceptions) topics. Delta between input and output delays should be the data processing time.

**/\*/\*/hz -** Output of "ros2 topic hz" of output topic (/perceptions). Shows message reception frequency on the topic.

**/\*/\*/prometheus -** CPU, memory and Networking usage data of ADAS and CPU stressor (when present) pods.

**/\*/\*/timestamps -** Unix timestamps of starting and and times for each test iteration.
