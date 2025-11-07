// Dynamic form handling
        $(document).ready(function() {
            // Formset management
            $('.add-form').click(function() {
                const formset = $(this).closest('.formset');
                const totalForms = $('#id_' + formset.data('prefix') + '-TOTAL_FORMS');
                const formCount = parseInt(totalForms.val());
                const emptyForm = formset.find('.empty-form').clone(true);
                
                emptyForm.html(emptyForm.html().replace(/__prefix__/g, formCount));
                emptyForm.removeClass('empty-form d-none');
                emptyForm.addClass('formset-form');
                
                // Clear input values in the new form
                emptyForm.find('input, textarea, select').val('');
                emptyForm.find('input[type="checkbox"]').prop('checked', false);
                
                formset.append(emptyForm);
                totalForms.val(formCount + 1);
                
                // Reinitialize any dynamic fields
                initializeDynamicFields();
            });

            $(document).on('click', '.remove-form', function() {
                const form = $(this).closest('.formset-form');
                const deleteField = form.find('input[id$="-DELETE"]');
                
                if (deleteField.length) {
                    // Mark for deletion
                    deleteField.val('on');
                    form.hide();
                } else {
                    form.remove();
                }
                updateFormIndexes();
            });

            function updateFormIndexes() {
                $('.formset').each(function() {
                    const prefix = $(this).data('prefix');
                    const forms = $(this).find('.formset-form:visible');
                    $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
                    
                    forms.each(function(index) {
                        $(this).find(':input').each(function() {
                            const name = $(this).attr('name').replace(/-\d+-/, '-' + index + '-');
                            const id = 'id_' + name;
                            $(this).attr({'name': name, 'id': id});
                        });
                        
                        $(this).find('label').each(function() {
                            const newFor = $(this).attr('for').replace(/-\d+-/, '-' + index + '-');
                            $(this).attr('for', newFor);
                        });
                    });
                });
            }

            // Initialize dynamic fields
            function initializeDynamicFields() {
                // Show/hide tender fields based on enquiry type
                function toggleTenderFields() {
                    const enquiryType = $('#id_enquiry_type').val();
                    const tenderFields = $('.tender-field');
                    const referralFields = $('.referral-field');
                    
                    if (enquiryType === 'tender') {
                        tenderFields.show();
                        referralFields.hide();
                    } else if (enquiryType === 'referral') {
                        tenderFields.hide();
                        referralFields.show();
                    } else {
                        tenderFields.hide();
                        referralFields.hide();
                    }
                }

                $('#id_enquiry_type').change(toggleTenderFields);
                toggleTenderFields(); // Initial call

                // Dynamic contact person loading
                $('#id_customer').change(function() {
                    const customerId = $(this).val();
                    if (customerId) {
                        $.ajax({
                            url: '{% url "crm:get_contact_persons" %}',
                            data: {
                                'customer_id': customerId
                            },
                            dataType: 'json',
                            success: function(data) {
                                $('#id_contact_person').empty();
                                $('#id_contact_person').append('<option value="">Select Contact Person</option>');
                                $.each(data, function(index, person) {
                                    $('#id_contact_person').append(
                                        $('<option></option>').attr('value', person.id).text(
                                            person.concern_person + ' - ' + (person.designation || 'No designation')
                                        )
                                    );
                                });
                            },
                            error: function() {
                                $('#id_contact_person').empty();
                                $('#id_contact_person').append('<option value="">Select Contact Person</option>');
                            }
                        });
                    } else {
                        $('#id_contact_person').empty();
                        $('#id_contact_person').append('<option value="">Select Contact Person</option>');
                    }
                });
            }

            // Initial initialization
            initializeDynamicFields();
        });

        // Print functionality
        function printDocument() {
            window.print();
        }
