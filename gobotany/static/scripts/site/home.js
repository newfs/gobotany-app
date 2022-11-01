require([
    "util/news"
], function (News) {
    $(document).ready(function () {
        var news = new News();
        news.showDialog();
    });
});
