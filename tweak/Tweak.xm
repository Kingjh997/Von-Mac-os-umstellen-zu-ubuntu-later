#import <UIKit/UIKit.h>

// Example only: logs when a Settings view appears.
// Logos' internal generator avoids requiring Substrate to compile this hook.
%config(generator=internal);

%hook UIViewController

- (void)viewDidAppear:(BOOL)animated {
    %orig;
    NSLog(@"[UbuntuDemo] View appeared: %@", NSStringFromClass([self class]));
}

%end
