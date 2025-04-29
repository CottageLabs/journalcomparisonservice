from django.shortcuts import redirect
from .utils import execute_psr_next_task


def check_if_psr_task_finished(redirect_url):
    """
    A decorator to check if existing workflow task has been completed.
    If completed, redirect to next available task.
    If the workflow is completed and no other task to perform, redirect to 'redirect_url'
    The chance that the task is invoked after completed is that, if the user tries to go
    back in the browser and do a refresh
    :param redirect_url: url or url id to redirect to if the workflow is complete
    """
    def decorator(func):
        def wrapper(request, **kwargs):
            if request.activation.status == 'DONE':
                result = execute_psr_next_task(request)
                if result:
                    return result
                else:
                    return redirect(redirect_url)
            else:
                return func(request, **kwargs)
        return wrapper
    return decorator

