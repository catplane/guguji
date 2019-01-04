var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = false;   // 是否正在向后台获取数据, false：没有人往后端请求数据，反之


$(function () {

    //TODO: 首次进入，去加载新闻列表数据
    updateNewsData()

    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid')
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        $(this).addClass('active')

        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        // 快滚动到页面的底部了，请求下一页的数据
        if ((canScrollHeight - nowScroll) < 100) {
            // TODO 判断页数，去更新新闻数据

            // 拉取多次请求一次的判断逻辑
            // 没有人在往后端请求数据
            if(!data_querying){


                if(cur_page <= total_page){

                    // 正在加载数据
                    data_querying = true
                   // 请求下一页数据
                    updateNewsData()
                }else{
                    // 页码越界了
                    data_querying = false

                }

            }

        }
    })
})

// 请求新闻列表数据
function updateNewsData() {
    var params = {
        "page": cur_page,
        "cid": currentCid,
        'per_page': 10
    }

    // ajax请求的简写
    $.get("/news_list", params, function (resp) {
        if (resp) {

            // 只有第一次才需要清除站位数据
            if(cur_page == 1){
              // 先清空原有数据
                $(".list_con").html('')
            }


            // 数据加载完毕，将data_querying设置成false表示没有人在加载数据，下一次下拉加载用能请求下一页的数据
            data_querying = false

            // 给总页数赋值
            total_page = resp.data.total_page
            // 页码递增
            cur_page += 1

            // 显示数据
            for (var i=0;i<resp.data.news_list.length;i++) {
                // 获取新闻字典
                var news = resp.data.news_list[i]
                var content = '<li>'
                content += '<a href="#" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="#" class="news_title fl">' + news.title + '</a>'
                content += '<a href="#" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                $(".list_con").append(content)
            }
        }
    })
}