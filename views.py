from ome_seadragon.ome_data import tags_data, projects_datasets
from ome_seadragon import settings
from ome_seadragon.slides_manager import RenderingEngineFactory

import logging
from distutils.util import strtobool
try:
    import simplejson as json
except ImportError:
    import json

from omeroweb.webclient.decorators import login_required

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render

logger = logging.getLogger(__name__)


def check_app(request):
    return HttpResponse("ome_seadragon working!")


def check_repository(request):
    if settings.IMGS_REPOSITORY:
        return HttpResponse(settings.IMGS_REPOSITORY)
    else:
        return HttpResponse("No repository has been configured")


@login_required()
def check_image_path(request, image_id, conn=None, **kwargs):
    return HttpResponse(slides_manager._get_image_path(image_id, conn))


def get_example_viewer(request, image_id):
    base_url = '%s://%s' % (request.META['wsgi.url_scheme'], request.META['HTTP_HOST'])
    return render(request, 'ome_seadragon/test/test_viewer.html',
                  {'image_id': image_id, 'host_name': base_url})


def get_example_annotations(request, image_id):
    base_url = '%s://%s' % (request.META['wsgi.url_scheme'], request.META['HTTP_HOST'])
    return render(request, 'ome_seadragon/test/test_annotations.html',
                  {'image_id': image_id, 'host_name': base_url})


def get_example_ome_rois(request, image_id):
    base_url = '%s://%s' % (request.META['wsgi.url_scheme'], request.META['HTTP_HOST'])
    return render(request, 'ome_seadragon/test/test_ome_roi.html',
                  {'image_id': image_id, 'host_name': base_url})


def get_example_custom_handlers(request, image_id):
    base_url = '%s://%s' % (request.META['wsgi.url_scheme'], request.META['HTTP_HOST'])
    return render(request, 'ome_seadragon/test/test_events.html',
                  {'image_id': image_id, 'host_name': base_url})


@login_required()
def get_projects(request, conn=None, **kwargs):
    try:
        fetch_datasets = strtobool(request.GET.get('datasets'))
    except (ValueError, AttributeError):
        fetch_datasets = False
    projects = projects_datasets.get_projects(conn, fetch_datasets)
    return HttpResponse(json.dumps(projects), content_type='application/json')


@login_required()
def get_project(request, project_id, conn=None, **kwargs):
    try:
        fetch_datasets = strtobool(request.GET.get('datasets'))
    except (ValueError, AttributeError):
        fetch_datasets = False
    try:
        fetch_images = strtobool(request.GET.get('images'))
    except (ValueError, AttributeError):
        fetch_images = False
    try:
        expand_series = strtobool(request.GET.get('full_series'))
    except (ValueError, AttributeError):
        expand_series = False
    project = projects_datasets.get_project(conn, project_id, fetch_datasets, fetch_images,
                                            expand_series)
    return HttpResponse(json.dumps(project), content_type='application/json')


@login_required()
def get_dataset(request, dataset_id, conn=None, **kwargs):
    try:
        fetch_images = strtobool(request.GET.get('images'))
    except (ValueError, AttributeError):
        fetch_images = False
    try:
        expand_series = strtobool(request.GET.get('full_series'))
    except (ValueError, AttributeError):
        expand_series = False
    dataset = projects_datasets.get_dataset(conn, dataset_id, fetch_images,
                                            expand_series)
    return HttpResponse(json.dumps(dataset), content_type='application/json')


@login_required()
def get_image(request, image_id, conn=None, **kwargs):
    try:
        fetch_rois = strtobool(request.GET.get('rois'))
    except (ValueError, AttributeError):
        fetch_rois = False
    image = projects_datasets.get_image(conn, image_id, fetch_rois)
    return HttpResponse(json.dumps(image), content_type='application/json')


@login_required()
def get_annotations(request, conn=None, **kwargs):
    try:
        fetch_images = strtobool(request.GET.get('fetch_imgs'))
    except (ValueError, AttributeError):
        fetch_images = False
    annotations = tags_data.get_annotations_list(conn, fetch_images)
    return HttpResponse(json.dumps(annotations), content_type='application/json')


@login_required()
def get_tagset(request, tagset_id, conn=None, **kwargs):
    try:
        fetch_tags = strtobool(request.GET.get('tags'))
    except (ValueError, AttributeError):
        fetch_tags = False
    try:
        fetch_images = strtobool(request.GET.get('images'))
    except (ValueError, AttributeError):
        fetch_images = False
    tagset = tags_data.get_tagset(conn, tagset_id, fetch_tags, fetch_images)
    return HttpResponse(json.dumps(tagset), content_type='application/json')


@login_required()
def get_tag(request, tag_id, conn=None, **kwargs):
    try:
        fetch_images = strtobool(request.GET.get('images'))
    except (ValueError, AttributeError):
        fetch_images = False
    tag = tags_data.get_tag(conn, tag_id, fetch_images)
    return HttpResponse(json.dumps(tag), content_type='application/json')


@login_required()
def find_annotations(request, conn=None, **kwargs):
    search_pattern = request.GET.get('query')
    try:
        fetch_images = strtobool(request.GET.get('fetch_imgs'))
    except (ValueError, AttributeError):
        fetch_images = False
    logger.debug('"fetch_imgs" value %r', fetch_images)
    annotations = tags_data.find_annotations(search_pattern, conn, fetch_images)
    return HttpResponse(json.dumps(annotations), content_type='application/json')


@login_required()
def get_image_dzi(request, image_id, conn=None, **kwargs):
    rendering_engine = RenderingEngineFactory().get_tiles_rendering_engine(image_id, conn)
    dzi_metadata = rendering_engine.get_dzi_description()
    if dzi_metadata:
        return HttpResponse(dzi_metadata, content_type='application/xml')
    else:
        return HttpResponseNotFound('No image with ID ' + image_id)


@login_required()
def get_image_thumbnail(request, image_id, conn=None, **kwargs):
    rendering_engine = RenderingEngineFactory().get_thumbnails_rendering_engine(image_id, conn)
    thumbnail, image_format = rendering_engine.get_thumbnail(int(request.GET.get('size')))
    if thumbnail:
        response = HttpResponse(content_type="image/%s" % image_format)
        thumbnail.save(response, image_format)
        return response
    else:
        return HttpResponseServerError('Unable to load thumbnail')


@login_required()
def get_tile(request, image_id, level, column, row, tile_format, conn=None, **kwargs):
    if tile_format != settings.DEEPZOOM_FORMAT:
        return HttpResponseServerError("Format %s not supported by the server" % tile_format)
    rendering_engine = RenderingEngineFactory().get_tiles_rendering_engine(image_id, conn)
    tile, image_format = rendering_engine.get_tile(int(level), int(column), int(row))
    if tile:
        response = HttpResponse(content_type='image/%s' % image_format)
        tile.save(response, image_format)
        return response
    else:
        return HttpResponseNotFound('No tile can be found')


@login_required()
def get_image_mpp(request, image_id, conn=None, **kwargs):
    rendering_engine = RenderingEngineFactory().get_tiles_rendering_engine(image_id, conn)
    image_mpp = rendering_engine.get_openseadragon_config()['mpp']
    return HttpResponse(json.dumps({'image_mpp': image_mpp}), content_type='application_json')
