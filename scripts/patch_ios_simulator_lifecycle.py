"""Adapt Unity 6000.2's exported simulator preview to the iOS 27 scene lifecycle.

This is scoped to the disposable simulator export, not a device release build.
Run after IosSimulatorBuild.Run and before xcodebuild.
"""
import argparse
import plistlib
from pathlib import Path

DELEGATE = r'''
// ApronLens simulator-only iOS 27 lifecycle bridge.
@interface ApronLensSimulatorSceneDelegate : UIResponder <UIWindowSceneDelegate>
@property(nonatomic, strong) UIWindow *window;
@end
@implementation ApronLensSimulatorSceneDelegate
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    if (![scene isKindOfClass:[UIWindowScene class]]) return;
    id app = UIApplication.sharedApplication.delegate;
    [app performSelector:NSSelectorFromString(@"initUnityWithApplication:") withObject:UIApplication.sharedApplication];
    self.window = [app valueForKey:@"window"];
    self.window.windowScene = (UIWindowScene *)scene;
    [self.window makeKeyAndVisible];
}
- (void)sceneDidBecomeActive:(UIScene *)scene {
    [UIApplication.sharedApplication.delegate applicationDidBecomeActive:UIApplication.sharedApplication];
}
- (void)sceneWillResignActive:(UIScene *)scene {
    [UIApplication.sharedApplication.delegate applicationWillResignActive:UIApplication.sharedApplication];
}
- (void)sceneDidEnterBackground:(UIScene *)scene {
    [UIApplication.sharedApplication.delegate applicationDidEnterBackground:UIApplication.sharedApplication];
}
- (void)sceneWillEnterForeground:(UIScene *)scene {
    [UIApplication.sharedApplication.delegate applicationWillEnterForeground:UIApplication.sharedApplication];
}
@end
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('export', type=Path)
    root = parser.parse_args().export
    path = root / 'Info.plist'
    data = plistlib.loads(path.read_bytes())
    data['UIApplicationSceneManifest'] = {
        'UIApplicationSupportsMultipleScenes': False,
        'UISceneConfigurations': {'UIWindowSceneSessionRoleApplication': [{
            'UISceneConfigurationName': 'ApronLens Simulator',
            'UISceneClassName': 'UIWindowScene',
            'UISceneDelegateClassName': 'ApronLensSimulatorSceneDelegate',
        }]},
    }
    path.write_bytes(plistlib.dumps(data))
    path = root / 'MainApp/main.mm'
    text = path.read_text()
    if '// ApronLens simulator-only' not in text:
        path.write_text(text + DELEGATE)
    path = root / 'Classes/UnityAppController.mm'
    text = path.read_text()
    old = '    [self initUnityWithApplication: application];\n    return YES;'
    new = '    // ApronLens: initialization moves to the scene connection callback.\n    return YES;'
    if old in text:
        path.write_text(text.replace(old, new, 1))
    elif new not in text:
        raise SystemExit('Unexpected Unity app delegate; inspect before patching.')
    # UIKit can request the keyboard during scene connection; reuse its lazy instance.
    path.write_text(path.read_text().replace('[KeyboardDelegate Initialize];', '[KeyboardDelegate Instance];'))
    print('Simulator scene lifecycle configured.')

if __name__ == '__main__':
    main()
