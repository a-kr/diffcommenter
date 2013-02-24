function init_diffpage() {
    var MINIMAL_PX_OFFSET_TO_CONSIDER_HEADER_CURRENT = $(window).height() / 2;

    function scroll_to_center_element_in_window(el) {
        var windowHeight = $(window).height();
        var elementHeight = el.height();

        var elementPosition = el.position();
        var elementTop = elementPosition.top;

        var toScroll = (windowHeight / 2) - (elementHeight / 2);

        window.scroll(0,(elementTop - toScroll));
        $('#horizontal_highlighter').css({'top': Math.round(elementTop - 1)}).show();
    }

    if (window.location.hash) {
        var anchor = $(window.location.hash);
        if (anchor) {
            setTimeout(function () {
                scroll_to_center_element_in_window(anchor);
            }, 0);
        }
    }

    function on_click_go_to_anchor_centered(e) {
        var link = $(e.currentTarget),
            anchor_el = $(link.attr('href'));
        if (e.button != 0) return;
        e.preventDefault();

        location.href = link.attr('href');
        scroll_to_center_element_in_window(anchor_el);
    }

    /* фиксируем наверху названия текущих коммита и файла */
    $(window).scroll(function () {
        var current_h3 = null, current_h4 = null;
        $('h3.commit').each(function() {
            var offtop = $(this).viewportOffset().top;
            if (offtop < MINIMAL_PX_OFFSET_TO_CONSIDER_HEADER_CURRENT) { current_h3 = this; }
        });
        $('h4.diff').each(function() {
            var offtop = $(this).viewportOffset().top;
            if (offtop < MINIMAL_PX_OFFSET_TO_CONSIDER_HEADER_CURRENT) { current_h4 = this; }
        });

        var set_fixed_link = function (link_to_set, destination_h) {
            if (!destination_h) return;
            $(link_to_set).text($('span', destination_h).text());
            $(link_to_set).attr('href', $('a', destination_h).attr('href'));
        };

        set_fixed_link('#current_h3_fixed', current_h3);
        set_fixed_link('#current_h4_fixed', current_h4);
    });

    $('.jumps-to-anchor').click(on_click_go_to_anchor_centered);
}
