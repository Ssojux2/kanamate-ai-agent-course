import gradio as gr


def test_gradio_apps_create_without_api_calls():
    from gradio_apps.week01_app import create_demo as week01
    from gradio_apps.week02_app import create_demo as week02
    from gradio_apps.week03_app import create_demo as week03
    from gradio_apps.week04_app import create_demo as week04
    from gradio_apps.week05_app import create_demo as week05
    from gradio_apps.week06_app import create_demo as week06

    for factory in [week01, week02, week03, week04, week05, week06]:
        demo = factory()
        assert isinstance(demo, gr.Blocks)

