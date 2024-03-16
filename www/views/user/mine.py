from django.shortcuts import render
from www import models
from utils.pager import Pagination
from utils.search_group import SearchGroup, Option


def mine_tran(request):
    group = SearchGroup(
        models.TransactionRecord,
        request,
        Option("charge_type", is_choice=True),
    )
    queryset = models.TransactionRecord.objects.filter(customer_id=request.nb_user.id).filter(
        **group.get_condition()).order_by("-id")
    pager = Pagination(request, queryset)

    context = {"pager": pager, "row_list": group.get_row_list()}
    return render(request, 'user/mine_tran.html', context)
