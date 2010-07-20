# TODO: need a more robust and consistent model for this. Dimensions should be
# replicated across both databases

def prep_year(year):
    year = int(year)
    if year < 100 and year >= 60:
        year += 1900
    if year < 60:
        year += 2000
    return year

def school_year_to_year(school_year):
    if not school_year or school_year == "":
        return None
    year1, year2 = school_year.split('-')
    return prep_year(year1)

def year_to_school_year(year):
    """Turn a 4 digit year into a school year in the form XXXX-YYYY """
    if not year or year == "":
        return None
    year = prep_year(year)
    next_year = year + 1
    return "%d-%d" % (year, next_year)
