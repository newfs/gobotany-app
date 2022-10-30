define([
    'bridge/jquery',
    'bridge/jquery.cookie'
], function ($, x1) {

    // Show a newsletter sign-up dialog periodically unless user dissmisses.

    function News() {
        this.subscribeUrl = "https://newenglandwild.us20.list-manage.com/" +
            "subscribe?u=da2ac32891c8517a5f7bca27c&id=f0bd3f3eb2";
    }

    News.prototype.shouldShowDialog = function () {
        var shouldShow = true;

        var showSignup = $.cookie("show_signup");
        var signupShown = $.cookie("signup_shown");

        if (showSignup && showSignup === "false") {
            // The user has previously asked not to show the dialog again.
            shouldShow = false;
        }
        else if (signupShown) {
            // The user has previously dismissed the dialog, but not
            // permanently; the cookie is still around, so don't show now.
            shouldShow = false;
        }
    
        return shouldShow;
    }

    News.prototype.dontShowAgain = function () {
        // Set the cookie to not show the dialog box again.
        var days = 365 * 10;   // effectively don't show again at all
        $.cookie("show_signup", "false", { expires: days, path: "/" });
    }

    News.prototype.signupShown = function () {
        // Set the cookie to allow the dialog box to be shown again later.
        var days = 14;   // days before showing again
        $.cookie("signup_shown", "true", { expires: days, path: "/" });
    }

    News.prototype.initEvents = function () {
        var that = this;
        $(".dialog__ok").on("click", function () {
            // If the user agrees to sign up for newsletters, assume
            // they will indeed sign up, so don't show the dialog again.
            that.dontShowAgain();
            $(".dialog").hide();
            window.location = that.subscribeUrl;
            return false;
        });
        $(".dialog__cancel, .dialog__close").on("click", function () {
            if ($("#dont-show-checkbox").prop("checked")) {
                // If the user checked the checkbox to not show again, honor
                // this whether they use either the cancel or close button.
                that.dontShowAgain();
            }
            else {
                // The cancel or close buttons (without the checkbox),
                // dismiss the dialog and suppress it for a period of time.
                that.signupShown();
            }
            $(".dialog").hide();
            return false;
        });
    }

    News.prototype.showDialog = function () {
        var shouldShow = this.shouldShowDialog();
        if (shouldShow) {
            $("body").append("<div class='dialog'>" +
                "<form method='GET' action=''>" +
                    "<h2>News from Native Plant Trust</h2>" +
                    "<p>Sign up for email newsletters from Native Plant " +
                        "Trust about conservation, horticulture, " +
                        "programs, and more.</p>" +
                    "<p><button class='dialog__ok'>Sign Up</button>" +
                        "<button class='dialog__cancel'>Not Now</button>" +
                        "<label class='dialog__check'>" +
                            "<input id='dont-show-checkbox' " +
                                "type='checkbox'>Don't show again</input>" +
                        "</label></p></form>" +
                "<button class='dialog__close' " +
                    "aria-label='Close'>×</button></div>");

            this.initEvents();
        }
    }

    return News;
});