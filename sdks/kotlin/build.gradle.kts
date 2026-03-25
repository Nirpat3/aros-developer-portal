plugins {
    kotlin("jvm") version "1.9.22"
    `maven-publish`
}

group = "com.aros"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}

kotlin {
    jvmToolchain(17)
}

java {
    withSourcesJar()
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            groupId = "com.aros"
            artifactId = "pos-sdk"
            version = project.version.toString()
            from(components["java"])

            pom {
                name.set("AROS POS SDK")
                description.set("Kotlin SDK for the AROS Connexus POS API — Android API 24+ and JVM server compatible")
                url.set("https://developer.aros.sh/sdks/kotlin")
                licenses {
                    license {
                        name.set("MIT")
                        url.set("https://opensource.org/licenses/MIT")
                    }
                }
                developers {
                    developer {
                        id.set("nirlab")
                        name.set("Nirlab Inc")
                        email.set("dev@nirlab.co")
                    }
                }
                scm {
                    url.set("https://github.com/nirlabinc/aros-developer-portal")
                }
            }
        }
    }
}
