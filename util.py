from core.indicators import indicator_list

def clean_value(val):
    if hasattr(val, 'strip') and callable(val.strip):
        val = val.strip()
        val = val.replace("%","")
        val = val.replace("#DIV/0!", '')
        val = val.replace("#NULL!", '')
    return val

def get_dynamic_indicator_def(metadata):
    for indicator_pair in indicator_list():
        if indicator_pair[0] == metadata['indicator_group'] + 'Indicator':
            return indicator_pair[1]

def new_generate_indicator_data(indicator, key_type, key_value, 
        time_type, time_key, value, data_type=None):
    from webportal.indicators.models import IndicatorData
    import datahub.indicators.conversion as conversion
    indicator_data_kwargs = {}
    
    value = clean_value(value)
    if data_type and data_type.lower() == 'text':
        data_type = 'text'
    elif data_type and data_type.lower() == 'numeric':
        data_type = 'numeric'
    else:
        try:
            float(value)
            data_type = 'numeric'
        except ValueError:
            data_type = 'text'
    indicator_data_kwargs['data_type'] = data_type
    
    if data_type == 'text':
        indicator_data_kwargs['string'] = value
    
    if data_type == 'numeric':
        if value == '':
            value = None
        indicator_data_kwargs['numeric'] = value
    
    indicator_data_kwargs['key_unit_type'] = key_type
    
    if key_type.upper() == 'SCHOOL':
        indicator_data_kwargs['key_value'] = key_value.rjust(5,'0')
    elif key_type.upper() == 'DISTRICT':
        indicator_data_kwargs['key_value'] = key_value.rjust(2,'0')
    else:
        indicator_data_kwargs['key_value'] = key_value
    
    indicator_data_kwargs['time_type'] = time_type
    indicator_data_kwargs['time_key'] = time_key
    indicator_data_kwargs['indicator'] = indicator
    return IndicatorData(**indicator_data_kwargs)

