package com.myidea.ui;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;

import com.google.android.material.bottomsheet.BottomSheetDialogFragment;
import com.myidea.R;
import com.myidea.viewmodel.IdeaViewModel;

public class AddIdeaSheet extends BottomSheetDialogFragment {

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.sheet_add_idea, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        View parent = (View) view.getParent();
        parent.setBackgroundColor(Color.TRANSPARENT);

        final EditText input = view.findViewById(R.id.input);
        View save = view.findViewById(R.id.save);
        View close = view.findViewById(R.id.close);

        final IdeaViewModel viewModel =
                new ViewModelProvider(requireActivity()).get(IdeaViewModel.class);

        save.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                viewModel.insert(input.getText().toString());
                dismiss();
            }
        });
        close.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dismiss();
            }
        });

        input.requestFocus();
        input.postDelayed(new Runnable() {
            @Override
            public void run() {
                InputMethodManager imm = (InputMethodManager)
                        requireContext().getSystemService(android.content.Context.INPUT_METHOD_SERVICE);
                if (imm != null) {
                    imm.showSoftInput(input, InputMethodManager.SHOW_IMPLICIT);
                }
            }
        }, 200);
    }
}
