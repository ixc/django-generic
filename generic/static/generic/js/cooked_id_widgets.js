(
    function($){
        $(document).ready(function(){
            window.update_cooked_field = function(field, is_inline_field, is_stacked_inline_field){
                if (!is_inline_field) is_inline_field = false;
                if (!is_stacked_inline_field) is_stacked_inline_field = false;
                $(field).hide();
                var container = "";
                if (is_inline_field && !is_stacked_inline_field) {
                    container = $(field).closest('td');
                } else {
                    container = $(field).closest('div');
                }
                $('.help', container).html(
                    'Click cross icons to remove existing items, ' +
                    'or magnifying glass icon to add more.'
                );
                var field_name = $(field).attr('name');
                var ids = escape($(field).val());
                if (ids){
                    var url_base = window.cooked_id_url_base || (
                        location.pathname.endsWith('/add/') ?
                            './' : '../'
                    );
                    var cook_url = "";
                    if (is_inline_field) {
                        var model_name = $(field).attr('data-model');
                        field_name = $(field).attr('data-field');
                        cook_url = url_base + 'cook-ids-inline/' + model_name + '/' + field_name + '/' + ids + '/';
                    } else {
                        cook_url = url_base + 'cook-ids/' + field_name + '/' + ids + '/';
                    }
                    $.get(cook_url, function(response){
                        var cooked = $('.cooked-data', container);
                        cooked.html('');
                        $.each(response, function(key, data){
                            if (is_inline_field) {
                                if (is_stacked_inline_field) {
                                    $('<li data-id="'+key+'"></li>').text(data['text']).append(
                                        ' <a onclick="remove_stacked_inline_cooked_item(this);"' +
                                        ' title="remove">&nbsp;</a>'
                                    ).appendTo(cooked);
                                } else {
                                    $('<li data-id="'+key+'"></li>').text(data['text']).append(
                                        ' <a onclick="remove_tabular_inline_cooked_item(this);"' +
                                        ' title="remove">&nbsp;</a>'
                                    ).appendTo(cooked);
                                }
                            } else {
                                $('<li data-id="'+key+'"></li>').text(data['text']).append(
                                    ' <a onclick="remove_cooked_item(this);"' +
                                    ' title="remove">&nbsp;</a>'
                                ).appendTo(cooked);
                            }

                            if(data['can_view'] || data['can_edit']) {
                                var options = {};
                                if(data['can_view'])
                                {
                                    options['View'] = {click: function(element) {
                                        window.location.href = data['can_view'];
                                    }}
                                }
                                if(data['can_edit']) {
                                    options['Edit'] = {click: function(element) {
                                        window.location.href = data['base_url'] + key + '/';
                                    }}
                                }

                                $('li[data-id='+key+']').contextMenu('context-menu-'+key, options);
                            }

														if(data['view_url'] || data['edit_url']) {
																var options = {};
																if(data['view_url'])
																{
																		options['View'] = {click: function(element) {
																				window.location.href = data['view_url'];
																			}
																		}
																}
																if(data['edit_url'])
																{
																		options['Edit'] = {click: function(element) {
																				window.location.href = data['edit_url'];
																			}
																		}
																}

																$('li[data-id='+key+']').contextMenu('context-menu-'+key, options);
														}

                        });
                    });
                }
            };

            window.remove_cooked_item = function(remove_link){
                var li = $(remove_link).parent();
                var id_to_remove = $(li).attr('data-id'); // jQuery only 1.4.2
                var container = $(li).closest('div');
                var field = $('.CookedIdField', container);
                var values = $(field).val().split(',');
                $(field).val(
                    $.grep(
                        values, function(id){ return id != id_to_remove }
                    ).join(',')
                );
                update_cooked_field(field);
                $(li).remove();
            }

            window.remove_tabular_inline_cooked_item = function(remove_link){
                var li = $(remove_link).parent();
                var id_to_remove = $(li).attr('data-id'); // jQuery only 1.4.2
                var container = $(li).closest('td');
                var field = $('.TabularInlineCookedIdField', container);
                var values = $(field).val().split(',');
                $(field).val(
                    $.grep(
                        values, function(id){ return id != id_to_remove }
                    ).join(',')
                );
                update_cooked_field(field, true);
                $(li).remove();
            }

            window.remove_stacked_inline_cooked_item = function(remove_link){
                var li = $(remove_link).parent();
                var id_to_remove = $(li).attr('data-id'); // jQuery only 1.4.2
                var container = $(li).closest('div');
                var field = $('.StackedInlineCookedIdField', container);
                var values = $(field).val().split(',');
                $(field).val(
                    $.grep(
                        values, function(id){ return id != id_to_remove }
                    ).join(',')
                );
                update_cooked_field(field, true, true);
                $(li).remove();
            }

            var originalDismissRelated = window.dismissRelatedLookupPopup;
            window.dismissRelatedLookupPopup = function(win, chosenId){
                originalDismissRelated(win, chosenId);
                $(window).trigger('dismissRelatedLookupPopup');
            }

            var originalDismissAddAnother = window.dismissAddAnotherPopup;
            window.dismissAddAnotherPopup = function(win, newId, newRepr){
                originalDismissAddAnother(win, newId, newRepr);
                $(window).trigger('dismissAddAnotherPopup');
            }

            $('.CookedIdField').each(
                function(index, element){
                    update_cooked_field(element);
                    $(element).bind(
                        'change', function(event){
                            update_cooked_field(event.target);
                        }
                    );
                }
            );
            $('.TabularInlineCookedIdField').each(
                function(index, element){
                    update_cooked_field(element, true);
                    $(element).bind(
                        'change', function(event){
                            update_cooked_field(event.target, true);
                        }
                    );
                }
            );
            $('.StackedInlineCookedIdField').each(
                function(index, element){
                    update_cooked_field(element, true, true);
                    $(element).bind(
                        'change', function(event){
                            update_cooked_field(event.target, true, true);
                        }
                    );
                }
            );
            $(window).bind('dismissRelatedLookupPopup', function(event){
                $('.CookedIdField, .TabularInlineCookedIdField, .StackedInlineCookedIdField').each(
                    function(index, element){
                        $(element).triggerHandler('change');
                    }
                );
            });
            $(window).bind('dismissAddAnotherPopup', function(event){
                $('.CookedIdField, .TabularInlineCookedIdField, .StackedInlineCookedIdField').each(
                    function(index, element){
                        $(element).triggerHandler('change');
                    }
                );
            });
        });
    }
)(django.jQuery);
