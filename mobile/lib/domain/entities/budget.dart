class BudgetEnvelope {
  final String id;
  final String name;
  final String code;
  final String status;
  final double totalAmount;
  final double allocatedAmount;
  final double spentAmount;
  final String currency;
  final String? ownerRole;
  final String? updatedAt;

  const BudgetEnvelope({
    required this.id,
    required this.name,
    required this.code,
    required this.status,
    required this.totalAmount,
    required this.allocatedAmount,
    required this.spentAmount,
    required this.currency,
    this.ownerRole,
    this.updatedAt,
  });

  double get availableAmount => totalAmount - spentAmount;

  factory BudgetEnvelope.fromJson(Map<String, dynamic> json) {
    return BudgetEnvelope(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? json['title']?.toString() ?? '',
      code: json['code']?.toString() ?? json['budget_code']?.toString() ?? '',
      status: json['status']?.toString() ?? 'draft',
      totalAmount: (json['total_amount'] as num?)?.toDouble() ??
          (json['budget_amount'] as num?)?.toDouble() ??
          0,
      allocatedAmount: (json['allocated_amount'] as num?)?.toDouble() ??
          (json['committed_amount'] as num?)?.toDouble() ??
          0,
      spentAmount: (json['spent_amount'] as num?)?.toDouble() ??
          (json['actual_spend'] as num?)?.toDouble() ??
          0,
      currency: json['currency']?.toString() ?? 'MAD',
      ownerRole: json['owner_role']?.toString(),
      updatedAt: json['updated_at']?.toString(),
    );
  }
}

class BudgetAllocation {
  final String id;
  final String budgetId;
  final String label;
  final double amount;
  final double committedAmount;
  final double spentAmount;
  final String currency;

  const BudgetAllocation({
    required this.id,
    required this.budgetId,
    required this.label,
    required this.amount,
    required this.committedAmount,
    required this.spentAmount,
    required this.currency,
  });

  factory BudgetAllocation.fromJson(Map<String, dynamic> json) {
    return BudgetAllocation(
      id: json['id']?.toString() ?? '',
      budgetId: json['budget_id']?.toString() ?? '',
      label: json['label']?.toString() ??
          json['category']?.toString() ??
          json['name']?.toString() ??
          '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      committedAmount: (json['committed_amount'] as num?)?.toDouble() ?? 0,
      spentAmount: (json['spent_amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency']?.toString() ?? 'MAD',
    );
  }
}

class BudgetRequest {
  final String id;
  final String allocationId;
  final String? budgetId;
  final String status;
  final double amount;
  final String currency;
  final String description;
  final String? justification;
  final String? requesterName;
  final String? createdAt;

  const BudgetRequest({
    required this.id,
    required this.allocationId,
    required this.status,
    required this.amount,
    required this.currency,
    required this.description,
    this.budgetId,
    this.justification,
    this.requesterName,
    this.createdAt,
  });

  factory BudgetRequest.fromJson(Map<String, dynamic> json) {
    return BudgetRequest(
      id: json['id']?.toString() ?? '',
      allocationId: json['allocation_id']?.toString() ?? '',
      budgetId: json['budget_id']?.toString(),
      status: json['status']?.toString() ?? 'pending',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency']?.toString() ?? 'MAD',
      description: json['description']?.toString() ?? '',
      justification: json['justification']?.toString(),
      requesterName:
          json['requester_name']?.toString() ?? json['requester']?.toString(),
      createdAt: json['created_at']?.toString(),
    );
  }
}

class BudgetTransaction {
  final String id;
  final String allocationId;
  final double amount;
  final String currency;
  final String direction;
  final String description;
  final String? createdAt;

  const BudgetTransaction({
    required this.id,
    required this.allocationId,
    required this.amount,
    required this.currency,
    required this.direction,
    required this.description,
    this.createdAt,
  });

  factory BudgetTransaction.fromJson(Map<String, dynamic> json) {
    return BudgetTransaction(
      id: json['id']?.toString() ?? '',
      allocationId: json['allocation_id']?.toString() ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency']?.toString() ?? 'MAD',
      direction: json['direction']?.toString() ?? 'outflow',
      description: json['description']?.toString() ?? '',
      createdAt: json['created_at']?.toString(),
    );
  }
}

class BudgetAnalytics {
  final double totalBudget;
  final double allocatedAmount;
  final double spentAmount;
  final double availableAmount;
  final int openRequests;

  const BudgetAnalytics({
    required this.totalBudget,
    required this.allocatedAmount,
    required this.spentAmount,
    required this.availableAmount,
    required this.openRequests,
  });

  factory BudgetAnalytics.fromJson(Map<String, dynamic> json) {
    return BudgetAnalytics(
      totalBudget: (json['total_budget'] as num?)?.toDouble() ??
          (json['budget_total'] as num?)?.toDouble() ??
          0,
      allocatedAmount: (json['allocated_amount'] as num?)?.toDouble() ?? 0,
      spentAmount: (json['spent_amount'] as num?)?.toDouble() ?? 0,
      availableAmount: (json['available_amount'] as num?)?.toDouble() ??
          (json['remaining_amount'] as num?)?.toDouble() ??
          0,
      openRequests: (json['open_requests'] as num?)?.toInt() ??
          (json['request_count'] as num?)?.toInt() ??
          0,
    );
  }
}

class BudgetDetailBundle {
  final BudgetEnvelope budget;
  final List<BudgetAllocation> allocations;
  final List<BudgetTransaction> transactions;
  final List<BudgetRequest> requests;
  final BudgetAnalytics analytics;

  const BudgetDetailBundle({
    required this.budget,
    required this.allocations,
    required this.transactions,
    required this.requests,
    required this.analytics,
  });
}
