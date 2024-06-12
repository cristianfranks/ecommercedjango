from django.shortcuts import redirect

def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('/admin/?next=' + request.path)
        else:
            return redirect('/admin/?next=' + request.path)
    return _wrapped_view_func