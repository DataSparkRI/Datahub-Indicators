import os

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse
from indicators.models import Indicator

def _collect_batch_info(uuid):
    path = './media/batches/%s/' % uuid
    return {
        'uuid': uuid,
        'finished': os.path.exists(os.path.join(path,'batch.tar.gz')),
        'num_indicators': len([entry for entry in os.listdir(path) if entry.endswith('.csv')]) / 2
    }

@staff_member_required
def indicator_batch_list(request):
    """ Displays the status of an indicator debug batch.

    The directory with the name specified by the uuid parameter is searched for
    output, debug and log files. Return 404 if not found. If log.txt exists, but
    the "end batch" marker isn't found, output the log file contents, but do not
    offer a download link.

    If the batch is complete, provide a tar/gzip of the files.
    """
    return render_to_response('admin/indicator_batch_list.html',
        {'batches': map(lambda b: _collect_batch_info(b), os.listdir('./media/batches/'))},
        context_instance=RequestContext(request))

@staff_member_required
def indicator_batch(request, uuid):
    """ Displays the status of an indicator debug batch.

    The directory with the name specified by the uuid parameter is searched for
    output, debug and log files. Return 404 if not found. If log.txt exists, but
    the "end batch" marker isn't found, output the log file contents, but do not
    offer a download link.

    If the batch is complete, provide a tar/gzip of the files.
    """
    pass


@staff_member_required
def regenerate_weave(request):
    try:
        from weave_addons.forms import RegenerateWeaveForm
    except ImportError:
        return

    # Update the weave database and attribute hierarchy
    process_id = None
    made_attempt = False
    if request.method == 'POST':
        form = RegenerateWeaveForm(data=request.POST)
        if form.is_valid():
            process_id = form.process()
            made_attempt = True
    else:
        form = RegenerateWeaveForm()
    return render_to_response(
        'admin/regenerate_weave.html',
        {'form': form,
         'made_attempt': made_attempt,
         'process_id': process_id,},
        context_instance=RequestContext(request)
    )

@staff_member_required
def batch_create(request):
    from commands import import_indicator_csv_task
    from django.contrib import messages
    import ucsv as csv
    if request.method == 'POST':
        next_url = request.POST.get('next')
        if 'indicator-data' in request.FILES:
            ind_file = request.FILES['indicator-data']
            if ind_file.name.endswith("csv"):
                # we need to write this file to the disk for moment
                # /tmp/filename works for now.
                fout = open('/tmp/%s' % ind_file.name, 'wb+')
                for chunk in ind_file.chunks():
                    fout.write(chunk)
                fout.close()
                t = import_indicator_csv_task(fout.name)
                messages.info(request, "Import task has started. Task ID: %s" % t.command.task_id)
        else:
            messages.error(request, "Please select a .csv file")

        return HttpResponseRedirect(next_url)
