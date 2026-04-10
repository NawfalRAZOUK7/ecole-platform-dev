allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

fun Project.configureMissingAndroidNamespace() {
    pluginManager.withPlugin("com.android.library") {
        val androidExtension = extensions.findByName("android") ?: return@withPlugin
        val getNamespace =
            androidExtension.javaClass.methods.firstOrNull { it.name == "getNamespace" }
                ?: return@withPlugin
        val setNamespace =
            androidExtension.javaClass.methods.firstOrNull { it.name == "setNamespace" }
                ?: return@withPlugin

        val currentNamespace = getNamespace.invoke(androidExtension) as String?
        if (!currentNamespace.isNullOrBlank()) {
            return@withPlugin
        }

        val manifestFile = file("src/main/AndroidManifest.xml")
        val manifestNamespace = if (manifestFile.exists()) {
            Regex("""package\s*=\s*"([^"]+)"""")
                .find(manifestFile.readText())
                ?.groupValues
                ?.getOrNull(1)
        } else {
            null
        }

        if (!manifestNamespace.isNullOrBlank()) {
            setNamespace.invoke(androidExtension, manifestNamespace)
        }
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
    configureMissingAndroidNamespace()
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
