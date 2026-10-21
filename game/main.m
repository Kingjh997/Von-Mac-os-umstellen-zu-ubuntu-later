#import <UIKit/UIKit.h>

@interface GameViewController : UIViewController
@property(nonatomic, strong) UILabel *titleLabel;
@property(nonatomic, strong) UILabel *scoreLabel;
@property(nonatomic, strong) UILabel *timeLabel;
@property(nonatomic, strong) UIButton *targetButton;
@property(nonatomic, strong) NSTimer *timer;
@property(nonatomic) NSInteger score;
@property(nonatomic) NSInteger secondsLeft;
@property(nonatomic) BOOL playing;
@end

@implementation GameViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor colorWithRed:0.055 green:0.09 blue:0.17 alpha:1.0];

    self.titleLabel = [[UILabel alloc] init];
    self.titleLabel.text = @"TAP SPRINT";
    self.titleLabel.textColor = UIColor.whiteColor;
    self.titleLabel.font = [UIFont systemFontOfSize:32 weight:UIFontWeightHeavy];
    self.titleLabel.textAlignment = NSTextAlignmentCenter;
    self.titleLabel.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.titleLabel];

    self.scoreLabel = [[UILabel alloc] init];
    self.scoreLabel.textColor = UIColor.whiteColor;
    self.scoreLabel.font = [UIFont systemFontOfSize:22 weight:UIFontWeightSemibold];
    self.scoreLabel.textAlignment = NSTextAlignmentCenter;
    self.scoreLabel.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.scoreLabel];

    self.timeLabel = [[UILabel alloc] init];
    self.timeLabel.textColor = [UIColor colorWithRed:0.55 green:0.83 blue:1 alpha:1];
    self.timeLabel.font = [UIFont monospacedDigitSystemFontOfSize:20 weight:UIFontWeightMedium];
    self.timeLabel.textAlignment = NSTextAlignmentCenter;
    self.timeLabel.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.timeLabel];

    self.targetButton = [UIButton buttonWithType:UIButtonTypeSystem];
    self.targetButton.backgroundColor = [UIColor colorWithRed:0.29 green:0.88 blue:0.69 alpha:1];
    [self.targetButton setTitleColor:[UIColor colorWithRed:0.03 green:0.12 blue:0.15 alpha:1] forState:UIControlStateNormal];
    [self.targetButton setTitle:@"START GAME" forState:UIControlStateNormal];
    self.targetButton.titleLabel.font = [UIFont systemFontOfSize:18 weight:UIFontWeightBold];
    self.targetButton.layer.cornerRadius = 32;
    self.targetButton.frame = CGRectMake(0, 0, 190, 64);
    [self.targetButton addTarget:self action:@selector(tapTarget) forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:self.targetButton];

    [NSLayoutConstraint activateConstraints:@[
        [self.titleLabel.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor constant:42],
        [self.titleLabel.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.scoreLabel.topAnchor constraintEqualToAnchor:self.titleLabel.bottomAnchor constant:20],
        [self.scoreLabel.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.timeLabel.topAnchor constraintEqualToAnchor:self.scoreLabel.bottomAnchor constant:8],
        [self.timeLabel.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor]
    ]];
    [self refreshLabels];
}

- (void)viewDidLayoutSubviews {
    [super viewDidLayoutSubviews];
    if (!self.playing && self.score == 0 && self.secondsLeft == 0) {
        self.targetButton.center = CGPointMake(CGRectGetMidX(self.view.bounds), CGRectGetMidY(self.view.bounds));
    }
}

- (void)refreshLabels {
    self.scoreLabel.text = [NSString stringWithFormat:@"SCORE  %ld", (long)self.score];
    self.timeLabel.text = self.secondsLeft > 0
        ? [NSString stringWithFormat:@"TIME  %ld", (long)self.secondsLeft]
        : @"30 seconds • tap the target";
}

- (void)tapTarget {
    if (!self.playing) {
        [self startGame];
        return;
    }
    self.score += 1;
    [self refreshLabels];
    [self moveTarget];
}

- (void)startGame {
    [self.timer invalidate];
    self.score = 0;
    self.secondsLeft = 30;
    self.playing = YES;
    [self.targetButton setTitle:@"TAP!" forState:UIControlStateNormal];
    [self refreshLabels];
    [self moveTarget];
    self.timer = [NSTimer scheduledTimerWithTimeInterval:1.0
                                                  target:self
                                                selector:@selector(tick)
                                                userInfo:nil
                                                 repeats:YES];
}

- (void)tick {
    self.secondsLeft -= 1;
    [self refreshLabels];
    if (self.secondsLeft <= 0) {
        [self.timer invalidate];
        self.timer = nil;
        self.playing = NO;
        [self.targetButton setTitle:@"PLAY AGAIN" forState:UIControlStateNormal];
        self.targetButton.center = CGPointMake(CGRectGetMidX(self.view.bounds), CGRectGetMidY(self.view.bounds));
        self.timeLabel.text = [NSString stringWithFormat:@"TIME UP  •  FINAL SCORE  %ld", (long)self.score];
    }
}

- (void)moveTarget {
    CGRect safe = self.view.safeAreaLayoutGuide.layoutFrame;
    CGFloat halfWidth = CGRectGetWidth(self.targetButton.bounds) / 2.0;
    CGFloat halfHeight = CGRectGetHeight(self.targetButton.bounds) / 2.0;
    CGFloat minX = CGRectGetMinX(safe) + halfWidth;
    CGFloat maxX = MAX(minX, CGRectGetMaxX(safe) - halfWidth);
    CGFloat minY = CGRectGetMinY(safe) + 150;
    CGFloat maxY = MAX(minY, CGRectGetMaxY(safe) - halfHeight - 20);
    CGFloat x = minX + (CGFloat)arc4random_uniform((uint32_t)MAX(1, (NSUInteger)(maxX - minX + 1)));
    CGFloat y = minY + (CGFloat)arc4random_uniform((uint32_t)MAX(1, (NSUInteger)(maxY - minY + 1)));
    self.targetButton.center = CGPointMake(x, y);
}

- (void)dealloc {
    [self.timer invalidate];
}

@end

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic, strong) UIWindow *window;
@end

@implementation AppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    (void)application;
    (void)launchOptions;
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    self.window.rootViewController = [[GameViewController alloc] init];
    [self.window makeKeyAndVisible];
    return YES;
}
@end

int main(int argc, char *argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass(AppDelegate.class));
    }
}
