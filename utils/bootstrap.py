class BootStrapForm:
    exclude_field_list = [] #如果想排除哪个字段不用这个样式，就把这个字段放在exclude_field_list 里面

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in self.exclude_field_list:
                continue
            field.widget.attrs['class'] = "form-control"
            field.widget.attrs['placeholder'] = "Please enter {}".format(field.label)