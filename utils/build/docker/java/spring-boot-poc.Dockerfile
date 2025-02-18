FROM maven:3.3-jdk-8 as build

WORKDIR /app
COPY ./utils/build/docker/java/spring-boot-poc/pom.xml .
RUN mkdir /maven && mvn -Dmaven.repo.local=/maven -B dependency:go-offline

COPY ./utils/build/docker/java/install_ddtrace.sh binaries* /binaries/
RUN /binaries/install_ddtrace.sh 

COPY ./utils/build/docker/java/spring-boot-poc/src ./src
RUN mvn -Dmaven.repo.local=/maven package

FROM adoptopenjdk:11-jre-hotspot

WORKDIR /app
COPY --from=build /binaries/SYSTEM_TESTS_LIBRARY_VERSION SYSTEM_TESTS_LIBRARY_VERSION 
COPY --from=build /app/target/myproject-0.0.1-SNAPSHOT.jar .
COPY --from=build /dd-tracer/dd-java-agent.jar .

CMD [ "java", "-javaagent:/app/dd-java-agent.jar", "-jar", "/app/myproject-0.0.1-SNAPSHOT.jar", "--server.port=7777" ]

# Datadog setup
ENV DD_TRACE_SAMPLE_RATE=0.5
ENV DD_TAGS='key1:val1, aKey : aVal bKey:bVal cKey:'
