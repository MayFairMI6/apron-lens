using System.IO;
using System.Xml;
using UnityEditor;
using UnityEditor.Android;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

// The development prototype talks to a local Mac over HTTP. Release builds do not opt in.
public class LocalModelAndroidNetwork : IPostGenerateGradleAndroidProject, IPreprocessBuildWithReport {
    static bool allowLocalHttp;
    public int callbackOrder => 100;
    public void OnPreprocessBuild(BuildReport report) {
        allowLocalHttp=(report.summary.options & BuildOptions.Development)!=0;
    }
    public void OnPostGenerateGradleAndroidProject(string path) {
        var file=Path.Combine(path,"src/main/AndroidManifest.xml");
        var document=new XmlDocument();document.Load(file);
        var application=(XmlElement)document.SelectSingleNode("/manifest/application");
        application.SetAttribute("usesCleartextTraffic","http://schemas.android.com/apk/res/android",
            allowLocalHttp?"true":"false");
        document.Save(file);
    }
}
