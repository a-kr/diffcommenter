function init_diffpage(opts) {
    opts.__proto__ = {
        'new_comment_url': '',
        'save_comment_url': '',
        'del_comment_url': '',
        'export_comments_url': '',
        'save_delay_ms': 1000
    };

    var MINIMAL_PX_OFFSET_TO_CONSIDER_HEADER_CURRENT = $(window).height() / 2;
    var ROW_HEIGHT = 16;
    var MAX_EXPORT_TEXTAREA_HEIGHT = 350;

    function scroll_to_center_element_in_window(el) {
        var windowHeight = $(window).height();
        var elementHeight = el.height();

        var elementPosition = el.position();
        var elementTop = elementPosition.top;

        var toScroll = (windowHeight / 2) - (elementHeight / 2);

        window.scroll(0,(elementTop - toScroll));
        $('#horizontal_highlighter').css({'top': Math.round(elementTop - 1)}).show();
    }

    $('td.line').bind('click', function () {
        $('#horizontal_highlighter').fadeOut();
    });

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
            $(link_to_set).attr('href', $('a.anchor-thingy', destination_h).attr('href'));
        };

        set_fixed_link('#current_h3_fixed', current_h3);
        set_fixed_link('#current_h4_fixed', current_h4);
    });

    $('.jumps-to-anchor').click(on_click_go_to_anchor_centered);

    /** выделение строк, создание комментариев **/

    /* информация о текущем выделении */
    var row_selection_context = {
        'mouse_down': false,
        'start_row': null,
        'end_row': null,
        'top_row': null,
        'bottom_row': null
    };

    /* изменение выделения */
    $('td.lno').bind('mousedown', function (ev) {
        var tr = $(ev.currentTarget).closest('tr');
        if (ev.button != 0) return;
        if (ev.target.tagName == 'A') return;
        ev.preventDefault();
        row_selection_context['mouse_down'] = true;
        row_selection_context['start_row'] = tr;
        row_selection_context['end_row'] = tr;
        update_rowspan_reticle();
    });
    $('td.lno').bind('mouseup', function (ev) {
        ev.preventDefault();
        row_selection_context['mouse_down'] = false;
        update_rowspan_reticle();
        create_new_comment();
    });
    $('td.lno').bind('mousemove', function (ev) {
        if (!row_selection_context['mouse_down']) return;
        ev.preventDefault();
        var tr = $(ev.currentTarget).closest('tr');
        row_selection_context['end_row'] = tr;
        update_rowspan_reticle();
    });

    /* определение, какая из выделенных строк наверху, а какая внизу */
    function get_top_and_bottom_row() {
        if (!row_selection_context['start_row'] || !row_selection_context['end_row']) {
            return null;
        }
        if (row_selection_context['start_row'].position().top <= row_selection_context['end_row'].position().top) {
            return {
                'top': row_selection_context['start_row'],
                'bottom': row_selection_context['end_row']
            }
        } else {
            return {
                'bottom': row_selection_context['start_row'],
                'top': row_selection_context['end_row']
            }
        }
    }

    /* изменение положения выделялки на экране */
    function update_rowspan_reticle() {
        var reticle = $('#rowspan_reticle'),
           rows = get_top_and_bottom_row();

        if (!rows) {
            reticle.hide();
            return;
        }
        var top_of_span = rows['top'].position().top,
            height_of_span = rows['bottom'].position().top + ROW_HEIGHT - top_of_span,
            some_td = $('td.line', rows['top']),
            left_of_span = some_td.position().left,
            width_of_span = some_td.width();
        reticle.css({
            'top': top_of_span,
            'left': left_of_span,
            'width': width_of_span,
            'height': height_of_span
        });

        reticle.show();
    }

    /* "ручной" способ заставить вылезти выделялку */
    function display_row_reticle(first_row, last_row) {
        row_selection_context['start_row'] = first_row;
        row_selection_context['end_row'] = last_row;
        update_rowspan_reticle();
    }

    /* "ручной" способ заставить спрятаться выделялку */
    function hide_row_reticle() {
        row_selection_context['start_row'] = null;
        row_selection_context['end_row'] = null;
        update_rowspan_reticle();
    }

    /* создание нового комментария к выделенному диапазону строк */
    function create_new_comment() {
        var rows = get_top_and_bottom_row();
        if (!rows) return;

        var diff_id = rows['bottom'].closest('table').data('diff-pk'),
            first_line_anchor = rows['top'].attr('id'),
            last_line_anchor = rows['bottom'].attr('id'),
            where_to_put_comment = $('td.line', rows['bottom']),
            comment_container = $('<div>').addClass('ajax_comment_container ajax_comment_container_loading')
                .text('loading..').appendTo(where_to_put_comment);

        $.ajax({
            'url': opts['new_comment_url'],
            'data': {
                'diff_id': diff_id,
                'first_line_anchor': first_line_anchor,
                'last_line_anchor': last_line_anchor
            },
            'complete': function (response, statusCode) {
                comment_container.removeClass('ajax_comment_container_loading');
                if (statusCode == 'error') {
                    response = response.responseText || 'Произошла неведомая и непонятная ошибка.';
                    comment_container.addClass('ajax_comment_container_error').text(response);
                    comment_container.click(function () {
                        comment_container.fadeOut(function () { $(this).remove(); });
                    });
                    setTimeout(function () {
                        comment_container.fadeOut(function () { $(this).remove(); });
                    }, 3000);
                } else {
                    $(comment_container).remove();
                    $(where_to_put_comment).append(response.responseText);
                    $('textarea', where_to_put_comment).last().focus();
                }
            }
        });
    }

    /* подсветка кода, относящегося к комменту, при наведении */
    $('.comment').live('mouseenter', function (ev) {
        var self = $(ev.currentTarget),
            first_row = $("#" + self.data('from')),
            last_row = $("#" + self.data('to'));
        display_row_reticle(first_row, last_row);
    });
    $('.comment').live('mouseleave', function (ev) {
        hide_row_reticle();
    });

    /* сохранение коммента */
    function save_comment(comment) {
        var comment_id = comment.data('pk'),
            comment_text = $('textarea', comment).val(),
            status_span = $('.save-status', comment);
        comment.data('save-timeout', null);
        status_span.text('♨');

        $.ajax({
            'url': opts['save_comment_url'],
            'type': 'POST',
            'data': {
                'comment_id': comment_id,
                'text': comment_text,
                'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']", comment).val()
            },
            'complete': function (response, statusCode) {
                if (statusCode == 'error') {
                    status_span.text('Save error');
                } else {
                    status_span.text('');
                }
            }
        });
    };

    /* автосохранение по изменениям, с задержкой */
    $('.comment textarea').live('keyup', function (ev) {
        var self = $(this),
            comment = self.closest('.comment'),
            timeout_id,
            old_timeout_id = comment.data('save-timeout');

        $('.save-status', comment).text('*');

        if (old_timeout_id) {
            clearTimeout(old_timeout_id);
        }
        timeout_id = setTimeout(function () {
            save_comment(comment);
        }, opts['save_delay_ms']);
        comment.data('save-timeout', timeout_id);
    });

    /* удаление коммента */
    $('.comment .del-comment a').live('click', function(ev) {
        var self = $(this),
            comment = self.closest('.comment'),
            comment_id = comment.data('pk'),
            status_span = $('.save-status', comment);
        status_span.text('Deleting...');
        ev.preventDefault();
        $.ajax({
            'url': opts['del_comment_url'],
            'type': 'POST',
            'data': {
                'comment_id': comment_id,
                'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']", comment).val()
            },
            'complete': function (response, statusCode) {
                if (statusCode == 'error') {
                    status_span.text('Delete error');
                } else {
                    comment.fadeOut(function () { comment.remove(); });
                }
            }
        });
        return false;
    });

    /* ответ на коммент (просто добавить новый коммент, ссылающийся на те же строки */
    $('.comment .reply-to-comment a').live('click', function(ev) {
        var self = $(this),
            comment = self.closest('.comment'),
            first_row = $("#" + comment.data('from')),
            last_row = $("#" + comment.data('to'));
        ev.preventDefault();
        display_row_reticle(first_row, last_row);
        create_new_comment();
        return false;
    });

    /* увеличиваем все поля для ввода комментов по содержимому */
    $('textarea').each(function (i, el) {
        $(el).css({
            'height': el.scrollHeight + ROW_HEIGHT
        });
    });

    /* прыжки к предыдущему и следующему комментам */
    $('a.prev-comment').live('click', function (ev) {
        var self = $(this),
            this_comment = self.closest('.comment'),
            this_comment_pos = this_comment.position().top,
            prev_comment = $('.comment').filter(function () {
                return ($(this).position().top < this_comment_pos);
            }).last();
        ev.preventDefault();
        if (prev_comment.length > 0) {
            location.href = '#' + prev_comment.attr('id');
            scroll_to_center_element_in_window(prev_comment);
        }
        return false;
    });
    $('a.next-comment').live('click', function (ev) {
        var self = $(this),
            this_comment = self.closest('.comment'),
            this_comment_pos = this_comment.position().top,
            next_comment = $('.comment').filter(function () {
                return ($(this).position().top > this_comment_pos);
            }).first();
        ev.preventDefault();
        if (next_comment.length > 0) {
            location.href = '#' + next_comment.attr('id');
            scroll_to_center_element_in_window($('.comment-title', next_comment));
        }
        return false;
    });

    /* экспорт комментов */
    $('#export_comments_btn').click(function (ev) {
        var textarea = $('#exported_comments');
        textarea.val('Loading...');
        $.ajax({
            'url': opts['export_comments_url'],
            'complete': function (response, statusText) {
                if (statusText == 'error') {
                    textarea.val('Export error. ' + response.responseText);
                } else {
                    textarea.val(response.responseText);
                    textarea.css({
                        'height': Math.min(textarea[0].scrollHeight + ROW_HEIGHT, MAX_EXPORT_TEXTAREA_HEIGHT)
                    });
                }
            }
        });
    });
}
