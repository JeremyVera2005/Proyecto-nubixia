# syntax=docker/dockerfile:1
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml ./
RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp dependency:go-offline
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp package

FROM eclipse-temurin:17-jre-alpine AS runtime
RUN apk add --no-cache fontconfig ttf-dejavu \
    && addgroup -S -g 10001 nubixia \
    && adduser -S -D -H -u 10001 -G nubixia nubixia \
    && mkdir -p /app/data && chown -R nubixia:nubixia /app
WORKDIR /app
COPY --from=build --chown=nubixia:nubixia /build/target/*-app.jar /app/app.jar
ENV PORT=8080 NUBIXIA_DATA_DIR=/app/data JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -Djava.awt.headless=true"
USER nubixia
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=45s --retries=5 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
